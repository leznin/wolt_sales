from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from database import WoltDatabase
import httpx
from datetime import datetime
import logging
from pathlib import Path
import asyncio
from itertools import chain
import random
import time
import sys
from urllib.parse import urlencode, urlparse
import json
import msgspec
from collections import defaultdict

# Добавляем поддержку SOCKS прокси
try:
    from httpx_socks import AsyncProxyTransport
    SOCKS_SUPPORT = True
except ImportError:
    SOCKS_SUPPORT = False
    print("Для поддержки SOCKS прокси установите: pip install httpx-socks")

@dataclass
class WoltConfig:
    """Конфигурация для WoltAPI"""
    save_responses: bool = False
    log_to_file: bool = False
    log_level: int = logging.INFO
    log_file: str = 'wolt_parser.log'
    use_http2: bool = True
    max_retries: int = 10
    base_delay: float = 0.5
    max_concurrent: int = 100
    request_timeout: int = 60
    respect_retry_after: bool = True
    use_cache: bool = True
    cache_ttl: int = 7200
    batch_size: int = 50
    min_retry_delay: float = 2.0
    max_retry_delay: float = 60.0
    # Новый параметр для управления количеством запросов к одному домену
    max_concurrent_per_domain: int = 5
    # Новый параметр для управления задержкой между запросами к одному домену
    domain_delay: float = 2.0

    def setup_logging(self):
        """Настройка логирования согласно конфигурации"""
        handlers = []
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        if self.log_to_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

        logging.basicConfig(
            level=self.log_level,
            handlers=handlers
        )

class WoltAPI:
    def __init__(self, lat: str, lon: str, config: Optional[WoltConfig] = None, db: Optional[WoltDatabase] = None, proxy: Optional[str] = None):
        self.lat = lat
        self.lon = lon
        self.proxy = proxy  # Добавляем поддержку прокси
        self.consumer_endpoint = "https://consumer-api.wolt.com/"
        self.restaurant_endpoint = "https://restaurant-api.wolt.com/v1/"
        
        
        # Список разнообразных User-Agent для запросов
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
        ]
        
        self.headers = {
            "User-Agent": random.choice(self.user_agents)
        }
        
        self.config = config or WoltConfig()
        self.config.setup_logging()
        self.db = db or WoltDatabase()
        self._request_count = 0
        self._rate_limit_semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        # Создаем семафоры для каждого домена
        self._domain_semaphores = defaultdict(lambda: asyncio.Semaphore(self.config.max_concurrent_per_domain))
        self._domain_last_request_time = defaultdict(float)
        
        self._last_request_time = 0
        self._client = None
        self._cache = {} if self.config.use_cache else None
        self._cache_timestamps = {} if self.config.use_cache else None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Получение или создание HTTP клиента с повторным использованием соединений"""
        if self._client is None or self._client.is_closed:
            use_http2 = self.config.use_http2 and not self.proxy  # HTTP/2 не поддерживается с SOCKS прокси
            
            limits = httpx.Limits(max_keepalive_connections=50, max_connections=100)
            timeout = httpx.Timeout(self.config.request_timeout)
            
            # С SOCKS прокси
            if self.proxy and SOCKS_SUPPORT:
                self._client = httpx.AsyncClient(
                    http2=False,  # HTTP/2 не поддерживается с SOCKS прокси в httpx
                    limits=limits,
                    timeout=timeout,
                    transport=AsyncProxyTransport.from_url(self.proxy)
                )
            # Без прокси или с HTTP прокси
            else:
                kwargs = {
                    "http2": use_http2,
                    "limits": limits,
                    "timeout": timeout
                }
                if self.proxy and not SOCKS_SUPPORT:
                    kwargs["proxies"] = {
                        "http://": self.proxy,
                        "https://": self.proxy
                    }
                
                self._client = httpx.AsyncClient(**kwargs)
        
        return self._client
    
    async def close(self):
        """Закрытие HTTP клиента"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def _get_from_cache(self, url: str) -> Optional[Dict]:
        """Получение данных из кэша"""
        if not self.config.use_cache or url not in self._cache:
            return None
        
        timestamp = self._cache_timestamps.get(url, 0)
        if time.time() - timestamp > self.config.cache_ttl:
            del self._cache[url]
            del self._cache_timestamps[url]
            return None
        
        return self._cache[url]
    
    def _add_to_cache(self, url: str, data: Dict) -> None:
        """Добавление данных в кэш"""
        if not self.config.use_cache:
            return
        
        self._cache[url] = data
        self._cache_timestamps[url] = time.time()
    
    async def _make_request(self, url: str, method: str = "GET", data: Dict = None, client: httpx.AsyncClient = None) -> Union[Dict, List]:
        """Выполнение запроса к API с ограничением скорости, повторными попытками и кэшированием"""
        if method == "GET" and self.config.use_cache:
            cached_data = self._get_from_cache(url)
            if cached_data is not None:
                return cached_data
        
        max_retries = self.config.max_retries
        base_delay = self.config.base_delay
        
        if client is None:
            client = await self._get_client()
        
        # Получаем домен из URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Обновляем User-Agent для каждого запроса
        headers = self.headers.copy()
        headers["User-Agent"] = random.choice(self.user_agents)
        
        # Используем два семафора: общий и для конкретного домена
        async with self._rate_limit_semaphore:
            async with self._domain_semaphores[domain]:
                # Проверяем время последнего запроса к этому домену
                current_time = time.time()
                domain_elapsed = current_time - self._domain_last_request_time[domain]
                if domain_elapsed < self.config.domain_delay:
                    await asyncio.sleep(self.config.domain_delay - domain_elapsed)
                
                # Проверяем общее время последнего запроса
                elapsed = current_time - self._last_request_time
                if elapsed < 1.0:
                    await asyncio.sleep(1.0 - elapsed)
                
                for retry in range(max_retries + 1):
                    try:
                        self._last_request_time = time.time()
                        self._domain_last_request_time[domain] = time.time()
                        self._request_count += 1
                        
                        if method == "GET":
                            response = await client.get(url, headers=headers, timeout=self.config.request_timeout)
                        else:
                            response = await client.post(url, headers=headers, json=data, timeout=self.config.request_timeout)
                        
                        if response.status_code == 200:
                            result = msgspec.json.decode(response.content)
                            if method == "GET" and self.config.use_cache:
                                self._add_to_cache(url, result)
                            await self._save_response_to_file(method, url, result)
                            return result
                        
                        elif response.status_code == 429:
                            # Улучшенная обработка TOO MANY REQUESTS
                            is_last_retry = retry >= max_retries
                            
                            # Извлекаем заголовок Retry-After, если он есть
                            retry_after = response.headers.get("Retry-After")
                            
                            # Рассчитываем время ожидания с экспоненциальной задержкой и jitter
                            if retry_after:
                                try:
                                    # Может быть числом секунд или датой в формате HTTP
                                    if retry_after.isdigit():
                                        wait_seconds = int(retry_after)
                                    else:
                                        # Обработка HTTP-даты
                                        retry_date = datetime.strptime(retry_after, "%a, %d %b %Y %H:%M:%S %Z")
                                        wait_seconds = max(1, (retry_date - datetime.now()).total_seconds())
                                    
                                    # Добавляем небольшой случайный jitter
                                    wait_time = wait_seconds + random.uniform(0.1, 1.0)
                                except (ValueError, OverflowError):
                                    # Если не удалось распарсить, используем экспоненциальную задержку
                                    wait_time = min(
                                        self.config.max_retry_delay,
                                        max(
                                            self.config.min_retry_delay,
                                            base_delay * (2 ** retry) + random.uniform(0.5, 2.0)
                                        )
                                    )
                            else:
                                # Если нет Retry-After, используем экспоненциальную задержку с ограничениями
                                wait_time = min(
                                    self.config.max_retry_delay,
                                    max(
                                        self.config.min_retry_delay,
                                        base_delay * (2 ** retry) + random.uniform(0.5, 2.0)
                                    )
                                )
                            
                            # Логируем информацию о повторной попытке
                            if is_last_retry:
                                logging.error(f"Превышено максимальное количество попыток ({max_retries}) для запроса к {url}: {response.reason_phrase}")
                            else:
                                logging.warning(f"Ошибка HTTP запроса к {url}: {response.reason_phrase}. Повторная попытка через {wait_time:.2f} секунд (попытка {retry+1}/{max_retries})")
                            
                            # Повторная попытка, если это не последняя итерация
                            if not is_last_retry:
                                await asyncio.sleep(wait_time)
                                continue
                            
                            return None
                        
                        else:
                            logging.error(f"Ошибка HTTP запроса к {url}: {response.reason_phrase}")
                            if 500 <= response.status_code < 600 and retry < max_retries:
                                wait_time = min(
                                    self.config.max_retry_delay,
                                    max(
                                        self.config.min_retry_delay,
                                        base_delay * (2 ** retry) + random.uniform(0.5, 2.0)
                                    )
                                )
                                logging.warning(f"Повторная попытка через {wait_time:.2f} секунд (попытка {retry+1}/{max_retries})")
                                await asyncio.sleep(wait_time)
                                continue
                            return None
                    
                    except (httpx.RequestError, httpx.TimeoutException) as e:
                        logging.error(f"Ошибка сети при выполнении запроса к {url}: {str(e)}")
                        if retry < max_retries:
                            wait_time = min(
                                self.config.max_retry_delay,
                                max(
                                    self.config.min_retry_delay,
                                    base_delay * (2 ** retry) + random.uniform(0.5, 2.0)
                                )
                            )
                            logging.warning(f"Повторная попытка через {wait_time:.2f} секунд (попытка {retry+1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        logging.error(f"Превышено максимальное количество попыток ({max_retries}) для запроса {url}")
                        return None
                
                    except Exception as e:
                        logging.error(f"Неожиданная ошибка при выполнении запроса к {url}: {str(e)}")
                        if retry < max_retries:
                            wait_time = min(
                                self.config.max_retry_delay,
                                max(
                                    self.config.min_retry_delay,
                                    base_delay * (2 ** retry) + random.uniform(0.5, 2.0)
                                )
                            )
                            logging.warning(f"Повторная попытка через {wait_time:.2f} секунд (попытка {retry+1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        logging.error(f"Превышено максимальное количество попыток ({max_retries}) для запроса {url}")
                        return None
        
        return None

    async def _save_response_to_file(self, method: str, url: str, data: Dict) -> None:
        """Сохраняет ответ API в JSON-файл"""
        if not self.config.save_responses:
            return
            
        try:
            responses_dir = Path("api_responses")
            responses_dir.mkdir(exist_ok=True)
            safe_url = url.replace("://", "_").replace("/", "_").replace("?", "_").replace("&", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{responses_dir}/{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Ошибка при сохранении ответа API в файл: {str(e)}")

    async def search_venues(self, query: str = "supermarket") -> List[Dict]:
        """Поиск магазинов"""
        venues = []
        venue_types = ["supermarket", "pharmacy"]
        
        for venue_type in venue_types:
            url = f"{self.consumer_endpoint}v1/pages/search"
            json_data = {
                "q": venue_type,
                "target": "venues",
                "lat": self.lat,
                "lon": self.lon
            }
            
            try:
                data = await self._make_request(url, "POST", json_data)
                if not data:
                    logging.error(f"Не удалось получить данные о магазинах типа {venue_type}")
                    continue
                
                city = data.get("city", "")
                section = data.get("sections", [])[0] if data.get("sections") else {}
                items = section.get("items", [])
                
                for item in items:
                    venue_data = item.get("venue", {})
                    venue_city = venue_data.get("city", "") or city
                    venue = {
                        "id": venue_data["id"],
                        "name": venue_data["name"],
                        "address": venue_data.get("address", ""),
                        "slug": venue_data["slug"],
                        "categories": venue_data.get("categories", []),
                        "lon": venue_data.get("location")[0],
                        "lat": venue_data.get("location")[1],
                        "city": venue_city,
                        "country": venue_data.get("country", ""),
                        "rating": venue_data.get("rating", {}),
                        "tags": venue_data.get("tags", []),
                        "image_url": item.get("image", {}).get("url"),
                        "short_description": venue_data.get("short_description"),
                        "venue_type": venue_type,
                        "currency": venue_data.get("currency", "")
                    }
                    venues.append(venue)
                
            except Exception as e:
                logging.error(f"Ошибка при поиске магазинов типа {venue_type}: {str(e)}")
        
        return venues

    async def get_venue_items(self, venue_slug: str, client: httpx.AsyncClient = None) -> List[Dict]:
        """Получение списка товаров магазина"""
        url = f"{self.consumer_endpoint}consumer-api/consumer-assortment/v1/venues/slug/{venue_slug}/assortment"
        params = {
            "unit_prices": "true",
            "show_weighted_items": "true",
            "show_subcategories": "true",
            "include_items": "true"
        }
        query_url = f"{url}?{urlencode(params)}"
        
        try:
            if client is None:
                client = await self._get_client()

            if self.config.use_cache:
                cached_data = self._get_from_cache(query_url)
                if cached_data is not None:
                    items = []
                    all_items = cached_data.get("items", [])
                    if isinstance(all_items, list) and all_items:
                        from concurrent.futures import ThreadPoolExecutor
                        def process_batch(batch):
                            batch_items = []
                            for item_data in batch:
                                self._process_item(item_data, batch_items, venue_slug, cached_data.get("id", ""))
                            return batch_items
                        batch_size = self.config.batch_size
                        batches = [all_items[i:i+batch_size] for i in range(0, len(all_items), batch_size)]
                        with ThreadPoolExecutor(max_workers=min(8, len(batches))) as executor:
                            batch_results = list(executor.map(process_batch, batches))
                        for batch_result in batch_results:
                            items.extend(batch_result)
                        return items
                    
                    categories = cached_data.get("categories", [])
                    if isinstance(categories, list):
                        for category in categories:
                            if not isinstance(category, dict):
                                continue
                            category_name = category.get("name", "")
                            category_id = category.get("id")
                            category_slug = category.get("slug")
                            if not category_id:
                                continue
                            category_url = f"{self.consumer_endpoint}consumer-api/consumer-assortment/v1/venues/slug/{venue_slug}/assortment/categories/slug/{category_slug}"
                            category_items = await self._fetch_category_items(category_url, category_name, venue_slug, cached_data.get("id", ""), client)
                            items.extend(category_items)
                    return items
            
            data = await self._make_request(query_url, client=client)
            items = []
            
            if not data or not isinstance(data, dict):
                logging.error(f"Не удалось получить данные для {venue_slug} или данные имеют неверный формат")
                return []
                
            venue_id = data.get("id", "")
            recommended_items = data.get("recommended_items", [])
            if isinstance(recommended_items, list):
                for item_data in recommended_items:
                    self._process_item(item_data, items, venue_slug, venue_id, "Recommended")
            
            all_items = data.get("items", [])
            if isinstance(all_items, list) and all_items:
                batch_size = self.config.batch_size
                for i in range(0, len(all_items), batch_size):
                    batch = all_items[i:i+batch_size]
                    for item_data in batch:
                        self._process_item(item_data, items, venue_slug, venue_id)
                return items
            
            categories = data.get("categories", [])
            if not isinstance(categories, list):
                logging.error(f"Категории имеют неверный формат для {venue_slug}")
                return items
                
            semaphore = asyncio.Semaphore(self.config.max_concurrent)
            
            async def fetch_with_rate_limit(category_url, category_name, venue_slug, venue_id):
                async with semaphore:
                    await asyncio.sleep(random.uniform(0.1, 0.5))
                    return await self._fetch_category_items(category_url, category_name, venue_slug, venue_id, client)
            
            category_tasks = []
            for category in categories:
                if not isinstance(category, dict):
                    continue
                category_name = category.get("name", "")
                category_id = category.get("id")
                category_slug = category.get("slug")
                if not category_id or not category_slug:
                    continue
                category_url = f"{self.consumer_endpoint}consumer-api/consumer-assortment/v1/venues/slug/{venue_slug}/assortment/categories/slug/{category_slug}"
                task = fetch_with_rate_limit(category_url, category_name, venue_slug, venue_id)
                category_tasks.append(task)
            
            if category_tasks:
                category_results = await asyncio.gather(*category_tasks, return_exceptions=True)
                for result in category_results:
                    if isinstance(result, Exception):
                        logging.error(f"Ошибка при получении товаров категории: {str(result)}")
                    elif isinstance(result, list):
                        items.extend(result)
            
            return items
        except Exception as e:
            logging.error(f"Ошибка при получении товаров магазина: {str(e)}")
            return []
    
    async def _fetch_category_items(self, category_url: str, category_name: str, venue_slug: str, venue_id: str, client: httpx.AsyncClient = None) -> List[Dict]:
        """Получение товаров для конкретной категории"""
        try:
            if self.config.use_cache:
                cached_data = self._get_from_cache(category_url)
                if cached_data is not None:
                    items = []
                    for item_data in cached_data.get("items", []):
                        self._process_item(item_data, items, venue_slug, venue_id, category_name)
                    return items
            
            category_data = await self._make_request(category_url, client=client)
            if not category_data:
                return []
            
            items = []
            if not isinstance(category_data.get("items"), list):
                return []
                
            for item_data in category_data.get("items", []):
                self._process_item(item_data, items, venue_slug, venue_id, category_name)
            
            return items
        except Exception as e:
            logging.error(f"Ошибка при получении товаров категории {category_name}: {str(e)}")
            return []
    
    def _process_item(self, item_data: Dict, items: List[Dict], venue_slug: str, venue_id: str, category_name: str = None) -> None:
        """Обработка данных товара и добавление в список"""
        try:
            if not item_data or not isinstance(item_data, dict):
                return
        
            # Получаем базовые цены из корневого объекта
            price = item_data.get("price")
            original_price = item_data.get("original_price")
        
            # Для обратной совместимости проверяем unit_price
            unit_price = item_data.get("unformatted_unit_price", {}) or {}
            if unit_price:
                price = unit_price.get("price", price)
                original_price = unit_price.get("original_price", original_price)
                logging.debug(f"unit_price {unit_price}")
        
            # Если price отсутствует, пропускаем
            if price is None:
                return
        
            # Приводим price к float
            try:
                price = float(price)
            except (ValueError, TypeError):
                return
        
                # Если original_price отсутствует или None, считаем, что скидки нет
            has_discount = False
            discount = 0
            final_price = price
            if original_price is not None:
                try:
                    original_price = float(original_price)
                    # Проверяем наличие скидки
                    if price < original_price:
                        discount = ((original_price - price) / original_price) * 100
                        has_discount = True
                        final_price = price
                    elif price > original_price:
                        discount = ((price - original_price) / price) * 100
                        has_discount = True
                        final_price = original_price
                except (ValueError, TypeError):
                    original_price = None  # Сбрасываем, если не удалось привести к float
        
            # Если категория не передана, берем из item_data или используем значение по умолчанию
            if category_name is None:
                category_name = item_data.get("category_name", "No category")
        
            # Предполагаем 2 знака после запятой по умолчанию
            currency_decimals = unit_price.get("currency_decimals", 2) if unit_price else 2
            price_divider = 10 ** currency_decimals
        
            # Обработка изображения
            images = item_data.get("images", [])
            image_url = None
            if images and isinstance(images, list) and len(images) > 0:
                image_url = images[0].get("url") if isinstance(images[0], dict) else images[0]
        
            # Формируем итоговый объект товара
            item = {
                "id": item_data.get("id", ""),
                "name": item_data.get("name", ""),
                "description": item_data.get("description", ""),
                "price": final_price / price_divider,
                "original_price": (original_price / price_divider) if original_price is not None else None,
                "base_price": None,  # Больше не используется, но оставляем для совместимости
                "discount_percentage": round(discount, 1) if has_discount else 0,
                "unit": unit_price.get("unit", "") if unit_price else "",
                "category": category_name,
                "venue_name": venue_slug,
                "venue_id": venue_id,
                "image_url": image_url,
                "available": item_data.get("purchasable_balance", 0) > 0 if item_data.get("purchasable_balance") is not None else True,
                "has_discount": has_discount,
            }
            items.append(item)
        
        except Exception as e:
            logging.error(f"Ошибка при обработке товара: {str(e)} цены {price} {original_price} id {item_data.get('id', '')}")

    async def search_discounted_items(self, min_discount: float = 1.0, max_concurrent: int = 5) -> List[Dict]:
        """Поиск товаров со скидкой с параллельной обработкой"""
        venues = await self.search_venues()
        if not venues:
            logging.error("Не удалось получить список магазинов")
            return []
        
        semaphore = asyncio.Semaphore(max_concurrent)
        client = await self._get_client()
        results = []
        
        async def process_venue(venue: Dict) -> Optional[Dict]:
            async with semaphore:
                try:
                    items = await self.get_venue_items(venue['slug'], client)
                    discounted_items = []
                    for item in items:
                        if item.get('discount_percentage', 0) >= min_discount:
                            discounted_items.append({
                                'id_venue': item.get('id'),
                                'name': item['name'],
                                'description': item.get('description', ''),
                                'category': item.get('category', ''),
                                'image_url': item.get('image_url', ''),
                                'current_price': item['price'],
                                'original_price': item['original_price'] if item['original_price'] is not None else None,
                                'base_price': item.get('baseprice'),
                                'discount_percentage': item['discount_percentage'],
                            })
                    
                    if discounted_items:
                        store_result = {
                            'store_id': venue['id'],
                            'store_name': venue['name'],
                            'slug': venue['slug'],
                            'lat': venue['lat'],
                            'lon': venue['lon'],
                            'city': venue.get('city', ''),
                            'venue_type': venue.get('venue_type', 'supermarket'),
                            'discounted_items': discounted_items,
                            'currency': venue.get('currency', '')
                        }
                        return store_result
                    return None
                except Exception as e:
                    logging.error(f"Ошибка при обработке магазина {venue.get('name', '')}: {str(e)}")
                    return None

        for venue in venues:
            result = await process_venue(venue)
            if result:
                store_data = {
                    'id_venue': result['store_id'],
                    'name': result['store_name'],
                    'slug': result['slug'],
                    'lat': float(result['lat']),
                    'lon': float(result['lon']),
                    'city': result.get('city', ''),
                    'image_url': result.get('image_url', ''),
                    'venue_type': result.get('venue_type', 'supermarket'),
                    'currency': result.get('currency', '')
                }
                self.db.update_store(store_data)
                
                discounted_items = result['discounted_items']
                batch_size = self.config.batch_size
                for i in range(0, len(discounted_items), batch_size):
                    batch = discounted_items[i:i+batch_size]
                    items_to_save = [
                        {
                            'id_venue': item['id_venue'],
                            'name': item['name'],
                            'description': item.get('description', ''),
                            'category': item.get('category', ''),
                            'image_url': item.get('image_url', ''),
                            'current_price': item['current_price'],
                            'original_price': item['original_price'],
                            'base_price': item.get('baseprice'),
                            'discount_percentage': item['discount_percentage'],
                        }
                        for item in batch
                    ]
                    self.db.update_discounted_items(result['store_id'], items_to_save)
                
                results.append(result)
        
        await client.aclose()
        
        if results:
            output_file = f"wolt_discounts_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results