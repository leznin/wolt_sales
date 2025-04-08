# file main.py
import asyncio
import logging
from wolt_api import WoltAPI, WoltConfig
from database import WoltDatabase
import time
from datetime import datetime
import os
import orjson  
import threading
import math
from typing import List, Optional


SAVE_RESPONSE_LOG = False   


db = WoltDatabase()

# получение proxy из базы с добавлением префикса socks5://
PROXY_LIST = [f"socks5://{p['proxy']}" for p in db.get_proxies_job()]



# Максимальное количество параллельных задач (по количеству прокси)
MAX_CONCURRENT_TASKS = len(PROXY_LIST)

# Глобальный счетчик для отслеживания статистики
stats = {
    "processed_stores": 0,
    "processed_items": 0,
    "discounted_items": 0,
    "saved_items": 0,
    "failed_stores": 0,
    "stores_with_errors": set(),
    "last_update": None
}

# Словарь для отслеживания нагрузки на прокси
proxy_stats = {}

# Интервал обновления магазинов (execution_delay)
STORE_UPDATE_INTERVAL_HOURS = float(db.get_setting("execution_delay")[0])


# Блокировка для обновления статистики
stats_lock = threading.Lock()

def update_stats(store_id=None, items_count=0, discounted_count=0, saved_count=0, failed=False):
    """Обновляет глобальную статистику и сохраняет ее в файл"""
    with stats_lock:
        if store_id and failed:
            stats["stores_with_errors"].add(store_id)
            stats["failed_stores"] += 1
        else:
            stats["processed_stores"] += 1
            stats["processed_items"] += items_count
            stats["discounted_items"] += discounted_count
            stats["saved_items"] += saved_count
        
        stats["last_update"] = datetime.now().isoformat()
        
        stats_json = stats.copy()
        stats_json["stores_with_errors"] = list(stats["stores_with_errors"])
        
        with open("processing_stats.json", "wb") as f:
            f.write(orjson.dumps(stats_json))

def update_proxy_stats(proxy_url):
    """Обновляет статистику использования прокси"""
    with stats_lock:
        proxy_key = proxy_url.split('@')[-1].split(':')[0]  # Извлекаем только IP-адрес прокси
        if proxy_key not in proxy_stats:
            proxy_stats[proxy_key] = 0
        proxy_stats[proxy_key] += 1

def print_progress_bar(processed, total):
    """Выводит шкалу прогресса и нагрузку по прокси в терминал"""
    bar_length = 40
    progress = processed / total if total > 0 else 0
    filled = int(bar_length * progress)
    bar = '#' * filled + '-' * (bar_length - filled)
    percent = progress * 100
    
    # Форматируем статистику по прокси более компактно
    proxy_load = ""
    if proxy_stats:
        # Извлекаем последние октеты IP для компактности
        shortened_stats = {}
        for ip, count in proxy_stats.items():
            # Получаем только последний октет IP для краткости
            short_ip = ip.split('.')[-1]  
            shortened_stats[short_ip] = count
        
        # Формируем короткую строку статистики
        proxy_load = " | Прокси: " + ", ".join([f"{ip}:{count}" for ip, count in shortened_stats.items()])
    
    print(f"\rПрогресс: [{bar}] {percent:.1f}% ({processed}/{total}){proxy_load}", end='', flush=True)

# Менеджер прокси для равномерного распределения прокси между задачами
class ProxyManager:
    def __init__(self, proxy_list):
        self.proxy_list = proxy_list
        self.proxy_index = 0
        self.lock = asyncio.Lock()
    
    async def get_proxy(self):
        async with self.lock:
            proxy = self.proxy_list[self.proxy_index]
            self.proxy_index = (self.proxy_index + 1) % len(self.proxy_list)
            # Обновляем статистику использования прокси
            update_proxy_stats(proxy)
            return proxy

async def get_stores_and_items():
    # Настройка логирования (только ключевые сообщения)
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler("wolt_processing.log")])
    
    db = WoltDatabase()
    config = WoltConfig(
        save_responses=SAVE_RESPONSE_LOG,
        log_level=logging.INFO,
        use_cache=True,
        max_concurrent=80
    )
    
    # Инициализируем менеджер прокси
    proxy_manager = ProxyManager(PROXY_LIST)
    
    # Создаем семафор для ограничения количества одновременных задач
    store_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
    
    # Получаем равномерно распределенные геопозиции из базы данных
    locations = db.get_evenly_spaced_locations(min_distance_km=1.5)
    if not locations:
        logging.warning("Не найдены геопозиции в базе данных. Используем стандартные координаты.")
        # Если локаций нет, используем стандартные координаты
        locations = [{"lat": "41.71991", "lon": "44.737911"}]
    
    try:
        print("Тест: Получение всех магазинов и сохранение всех товаров")
        start_time = datetime.now()
        
        all_stores = []
        # Обрабатываем каждую геопозицию последовательно
        for location_index, location in enumerate(locations):
            lat = str(location['lat'])
            lon = str(location['lon'])
            
            print(f"\nОбработка геопозиции [{location_index + 1}/{len(locations)}] - Координаты: {lat}, {lon}")
            # Используем случайный прокси для получения списка магазинов
            proxy = PROXY_LIST[location_index % len(PROXY_LIST)]
            api = WoltAPI(lat=lat, lon=lon, config=config, db=db, proxy=proxy)
            
            print(f"Получение списка магазинов для координат {lat}, {lon}...")
            stores = await api.search_venues()
            
            if not stores:
                print(f"Для координат {lat}, {lon} магазины не найдены")
                continue
            
            print(f"Найдено {len(stores)} магазинов для координат {lat}, {lon}")
            
            # Добавляем только новые магазины (которых ещё нет в общем списке)
            existing_ids = {store['id'] for store in all_stores}
            new_stores = [store for store in stores if store['id'] not in existing_ids]
            all_stores.extend(new_stores)
            
            print(f"Добавлено {len(new_stores)} новых магазинов. Всего уникальных магазинов: {len(all_stores)}")
            
            # Закрываем клиент API после использования
            await api.close()
        
        if not all_stores:
            print("Ошибка: Магазины не найдены ни для одной из геопозиций")
            return
        
        total_stores = len(all_stores)
        print(f"Всего найдено {total_stores} уникальных магазинов, обрабатываем все:")
        
        for i, store in enumerate(all_stores[:10], 1):
            print(f"{i}. Магазин: {store['name']} (slug: {store['slug']})")
        
        async def process_store(store, proxy, lat, lon):
            store_start_time = time.time()
            store_id = store['id']
            store_name = store['name']
            store_status = "success"
            
            total_items_count = 0
            discounted_items_count = 0
            saved_items_count = 0
            
            try:
                if db.is_store_recently_updated(store_id, STORE_UPDATE_INTERVAL_HOURS):
                    print(f"\rМагазин {store_name} уже обновлялся недавно. Пропускаем.", end='', flush=True)
                    existing_items = db.get_store_discounts(store_id)
                    discounted_items_count = len(existing_items)
                    
                    return 0, discounted_items_count, discounted_items_count, "skipped"

                # Создаем отдельный экземпляр API для каждого магазина с выделенным прокси
                api = WoltAPI(lat=lat, lon=lon, config=config, db=db, proxy=proxy)
                
                items = await api.get_venue_items(store['slug'])
                total_items_count = len(items)
                
                store_data = {
                    'id_venue': store_id,
                    'name': store_name,
                    'slug': store['slug'],
                    'lat': store['lat'],
                    'lon': store['lon'],
                    'city': store.get('city', ''),
                    'country': store.get('country', ''),
                    'image_url': store.get('image_url', ''),
                    'currency': store.get('currency', ''),
                    'venue_type': store.get('venue_type', 'supermarket')
                }
                
                db.update_store(store_data, update_timestamp=False)
                
                items_to_save = []
                for item in items:
                    if item.get('has_discount', False):
                        discounted_items_count += 1
                        item_data = {
                            'id_venue': item['id'],
                            'name': item['name'],
                            'description': item.get('description', ''),
                            'category': item.get('category', ''),
                            'image_url': item.get('image_url', ''),
                            'current_price': item['price'],
                            'original_price': item['original_price'] if item['original_price'] is not None else 0,
                            'base_price': item.get('base_price'),
                            'discount_percentage': item['discount_percentage'],
                        }
                        items_to_save.append(item_data)
                
                if items_to_save:
                    saved_count = db.update_discounted_items(store_id, items_to_save)
                    saved_items_count = saved_count if saved_count is not None else 0
                    db.mark_store_as_updated(store_id)
                else:
                    db.mark_store_as_updated(store_id)
                
                # Закрываем клиент API после использования
                await api.close()
                
                update_stats(items_count=total_items_count, discounted_count=discounted_items_count, saved_count=saved_items_count)
                
                return total_items_count, discounted_items_count, saved_items_count, store_status
            except Exception as e:
                store_status = "error"
                logging.error(f"Ошибка при обработке магазина {store_name}: {str(e)}")
                print(f"\rОшибка при обработке магазина {store_name}: {str(e)}", end='', flush=True)
                
                update_stats(store_id=store_id, failed=True)
                
                return 0, 0, 0, "error"
        
        # Обертка для process_store с использованием семафора
        async def process_store_with_semaphore(store):
            # Используем семафор для ограничения числа одновременных задач
            async with store_semaphore:
                # Получаем прокси из пула
                proxy = await proxy_manager.get_proxy()
                
                # Используем координаты магазина для запросов или первую локацию, если нет данных
                lat = str(store.get('lat', locations[0]['lat']))
                lon = str(store.get('lon', locations[0]['lon']))
                
                return await process_store(store, proxy, lat, lon)
        
        print(f"\nЗапуск параллельной обработки {total_stores} магазинов...")
        
        # Создаем задачи для всех магазинов
        tasks = []
        for store in all_stores:
            task = process_store_with_semaphore(store)
            tasks.append(task)
        
        # Запускаем все задачи параллельно
        processed_stores = 0
        results = []
        
        # Запускаем задачи и отслеживаем их выполнение
        pending = set(asyncio.create_task(task) for task in tasks)
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            
            for task in done:
                try:
                    result = task.result()
                    results.append(result)
                    processed_stores += 1
                    print_progress_bar(processed_stores, total_stores)
                except Exception as e:
                    logging.error(f"Ошибка в задаче: {str(e)}")
                    results.append((0, 0, 0, "error"))
                    processed_stores += 1
                    print_progress_bar(processed_stores, total_stores)
        
        print()  # Переход на новую строку после прогресс-бара
        
        total_items = sum(r[0] for r in results)
        total_discounted = sum(r[1] for r in results)
        total_saved = sum(r[2] for r in results)
        
        success_count = sum(1 for r in results if r[3] == "success")
        verification_failed = sum(1 for r in results if r[3] == "verification_failed")
        error_count = sum(1 for r in results if r[3] == "error")
        skipped_count = sum(1 for r in results if r[3] == "skipped")
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        print("\nПроверка данных в базе:")
        stores_count = db.get_stores_count()
        items_count = db.get_items_count()
        
        db_verification_success = (total_saved == items_count)
        
        print(f"\nИтоги теста:")
        print(f"Всего магазинов: {total_stores}")
        print(f"Успешно обработано: {success_count}")
        print(f"С ошибками верификации: {verification_failed}")
        print(f"С ошибками выполнения: {error_count}")
        print(f"Пропущено магазинов: {skipped_count}")
        print(f"Всего товаров: {total_items}")
        print(f"Всего товаров со скидкой: {total_discounted}")
        print(f"Всего сохранено товаров со скидкой: {total_saved}")
        print(f"Магазинов в базе: {stores_count}")
        print(f"Товаров со скидкой в базе: {items_count}")
        print(f"Проверка соответствия БД: {'УСПЕШНО' if db_verification_success else 'ОШИБКА'}")
        print(f"Общее время выполнения: {total_time:.2f} секунд")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_stores": total_stores,
            "processed_successfully": success_count,
            "verification_failed": verification_failed,
            "processing_errors": error_count,
            "skipped_stores": skipped_count,
            "total_items": total_items,
            "total_discounted_items": total_discounted,
            "total_saved_items": total_saved,
            "db_stores_count": stores_count,
            "db_items_count": items_count,
            "db_verification": "SUCCESS" if db_verification_success else "FAILED",
            "execution_time_seconds": total_time
        }
        
        with open("test_report.json", "wb") as f:
            f.write(orjson.dumps(report))
        
        if not db_verification_success:
            logging.warning(f"ВНИМАНИЕ! Несоответствие в количестве товаров: сохранено {total_saved}, в базе {items_count}")
        
    except Exception as e:
        logging.error(f"Ошибка при выполнении теста: {str(e)}")
        print(f"Ошибка при выполнении теста: {str(e)}")
    finally:
        await db.close()
        print("Тест завершен, ресурсы освобождены")

if __name__ == "__main__":
    asyncio.run(get_stores_and_items())