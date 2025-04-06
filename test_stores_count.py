# file test_stores_count.py
import asyncio
import logging
from wolt_api import WoltAPI, WoltConfig
from database import WoltDatabase
from datetime import datetime
import json

# Количество магазинов для проверки
STORES_COUNT_TO_CHECK = 5

# Интервал обновления магазина в часах
STORE_UPDATE_INTERVAL_HOURS = 12

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_stores_count.log"),
        logging.StreamHandler()
    ]
)

async def test_stores_count():
    """Тестовая функция для проверки указанного количества магазинов."""
    db = WoltDatabase()
    config = WoltConfig(
        save_responses=True,  # Включаем сохранение ответов API для отладки
        log_level=logging.DEBUG,
        use_cache=False,  # Отключаем кэш для свежих данных
        max_concurrent=20
    )
    api = WoltAPI(lat="41.71991", lon="44.737911", config=config, db=db)
    
    try:
        start_time = datetime.now()
        logging.info(f"Старт теста: проверка {STORES_COUNT_TO_CHECK} магазинов")
        
        # Получение списка магазинов
        stores = await api.search_venues()
        logging.info(f"Получено {len(stores)} магазинов от API")
        if not stores:
            logging.error("Не удалось получить список магазинов")
            return False
        
        total_stores = len(stores)
        stores_to_check = [
            store for store in stores 
            if not db.is_store_recently_updated(store['id'], STORE_UPDATE_INTERVAL_HOURS)
        ][:STORES_COUNT_TO_CHECK]
        
        stores_selected = len(stores_to_check)
        logging.info(f"Выбрано {stores_selected} магазинов для проверки из {total_stores} доступных")
        if stores_selected == 0:
            logging.info("Все магазины недавно обновлены, пропускаем обработку")
            return True
        
        # Статистика
        test_stats = {
            "total_stores_found": total_stores,
            "stores_checked": 0,
            "stores_skipped": total_stores - stores_selected,
            "stores_with_items": 0,
            "total_items_found": 0,
            "stores_with_discounts": 0,
            "total_discounted_items": 0,
            "stores_with_errors": []
        }
        
        # Обработка магазинов
        for i, store in enumerate(stores_to_check, 1):
            store_id = store['id']
            store_name = store['name']
            
            logging.info(f"Начало обработки магазина {i}/{stores_selected}: {store_name} (ID: {store_id})")
            try:
                items = await api.get_venue_items(store['slug'])
                logging.info(f"Получено {len(items)} товаров для магазина {store_name}")
                
                if not items:
                    logging.warning(f"Нет товаров для магазина {store_name}")
                    continue
                
                total_items = len(items)
                discounted_items = [item for item in items if item.get('has_discount', False)]
                discounted_count = len(discounted_items)
                logging.info(f"Найдено {discounted_count} товаров со скидкой из {total_items} для магазина {store_name}")
                
                test_stats["stores_checked"] += 1
                test_stats["stores_with_items"] += 1
                test_stats["total_items_found"] += total_items
                if discounted_count > 0:
                    test_stats["stores_with_discounts"] += 1
                    test_stats["total_discounted_items"] += discounted_count
                
                # Сохранение данных магазина
                store_data = {
                    'id_venue': store_id,
                    'name': store_name,
                    'slug': store['slug'],
                    'lat': store['lat'],
                    'lon': store['lon'],
                    'city': store.get('city', ''),
                    'image_url': store.get('image_url', 'test'),
                    'venue_type': store.get('venue_type', 'supermarket'),
                    'currency': store.get('currency', '~')
                }
                logging.info(f"Сохранение данных магазина {store_name}")
                db.update_store(store_data, update_timestamp=False)
                
                # Сохранение товаров со скидкой
                if discounted_items:
                    items_to_save = [
                        {
                            'id_venue': item['id'],
                            'name': item['name'],
                            'description': item.get('description', ''),
                            'category': item.get('category', ''),
                            'image_url': item.get('image_url', ''),
                            'current_price': item['price'],
                            'original_price': item['original_price'] or 0,
                            'base_price': item.get('base_price'),
                            'discount_percentage': item['discount_percentage'],
                        }
                        for item in discounted_items
                    ]
                    logging.info(f"Сохранение {len(items_to_save)} товаров со скидкой для магазина {store_name}")
                    inserted_count = db.update_discounted_items(store_id, items_to_save)
                    logging.info(f"Вставлено {inserted_count} товаров для магазина {store_name}")
                else:
                    logging.info(f"Нет товаров со скидкой для сохранения в магазине {store_name}")
                
                db.mark_store_as_updated(store_id)
                logging.info(f"Магазин {store_name} успешно обработан")
                
            except Exception as e:
                logging.error(f"Ошибка обработки магазина {store_name}: {str(e)}", exc_info=True)
                test_stats["stores_with_errors"].append({"id": store_id, "name": store_name, "error": str(e)})
        
        # Итоги
        execution_time = (datetime.now() - start_time).total_seconds()
        test_stats["execution_time_seconds"] = execution_time
        
        with open("test_stores_count_report.json", "w", encoding='utf-8') as f:
            json.dump(test_stats, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Тест завершен: проверено {test_stats['stores_checked']}/{stores_selected} магазинов за {execution_time:.2f} сек")
        return test_stats["stores_checked"] > 0
    
    except Exception as e:
        logging.error(f"Критическая ошибка теста: {str(e)}", exc_info=True)
        return False
    
    finally:
        await api.close()
        db.close()

if __name__ == "__main__":
    result = asyncio.run(test_stores_count())
    print(f"\n{'✅ Тест успешен' if result else '❌ Тест провален'}")