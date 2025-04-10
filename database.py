# file database.py
import mysql.connector
from mysql.connector import pooling
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import threading
import os
import math
from dotenv import load_dotenv
import json
import requests
from typing import Tuple

# Загрузка переменных из .env файла
load_dotenv()

# Конфигурация базы данных из .env
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "696578"),
    "database": os.getenv("DB_NAME", "wolt_sale"),
}

class ConnectionPool:
    """Simple connection pool for MySQL connections"""
    def __init__(self, max_connections: int = 5, timeout: int = 30):
        self.max_connections = max_connections
        self.timeout = timeout
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="wolt_pool",
            pool_size=max_connections,
            **DB_CONFIG
        )
        self.lock = threading.Lock()
    
    def get_connection(self) -> mysql.connector.MySQLConnection:
        """Get a connection from the pool"""
        try:
            return self.pool.get_connection()
        except mysql.connector.Error as e:
            logging.error(f"Error getting connection from pool: {e}")
            raise
    
    def release_connection(self, conn: mysql.connector.MySQLConnection):
        """Release a connection back to the pool"""
        if conn and conn.is_connected():
            conn.close()
    
    def close_all(self):
        """Close all connections in the pool"""
        try:
            self.pool._remove_connections()
        except Exception as e:
            logging.error(f"Error closing connection pool: {e}")

class WoltDatabase:
    def __init__(self, pool_size: int = 5):
        self.pool = ConnectionPool(max_connections=pool_size)
        self._init_db()
        
    def migrate_database(self):
        """Миграция базы данных для добавления поддержки валют и обновления структуры."""
        logging.info("Проверка необходимости миграции базы данных...")
        
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            
            # Проверяем наличие таблиц
            cursor.execute("SHOW TABLES LIKE 'stores'")
            stores_exists = cursor.fetchone() is not None
            
            if not stores_exists:
                logging.info("База данных пуста, миграция не требуется")
                return
                
            # Проверяем структуру таблицы stores
            cursor.execute("DESCRIBE stores")
            columns = {col[0] for col in cursor.fetchall()}
            
            if 'updated_at' not in columns and 'last_updated' in columns:
                logging.info("Обновление структуры таблицы stores")
                cursor.execute("""
                    ALTER TABLE stores 
                    CHANGE COLUMN last_updated updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
                logging.info("Таблица stores успешно обновлена")
            
            conn.commit()
            logging.info("Миграция базы данных успешно завершена")
            
        except Exception as e:
            logging.error(f"Ошибка при миграции базы данных: {str(e)}")
            if conn.in_transaction:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def _init_db(self):
        """Initialize database tables if they don't exist."""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()

            # Создание таблиц
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS stores (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255),
                slug VARCHAR(255),
                lat DOUBLE,
                lon DOUBLE,
                city VARCHAR(100),
                country VARCHAR(100),
                image_url VARCHAR(512),
                currency VARCHAR(10),
                venue_type VARCHAR(50) DEFAULT 'supermarket',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS discounted_items (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                id_venue VARCHAR(255),
                store_id VARCHAR(255),
                name VARCHAR(255),
                description TEXT,
                image_url VARCHAR(512),
                current_price DOUBLE,
                original_price DOUBLE,
                base_price DOUBLE,
                discount_percentage DOUBLE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE
            )
            ''')

            # Создаем таблицу категорий
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                venue_id VARCHAR(255),
                category_id VARCHAR(255),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (venue_id) REFERENCES stores(id) ON DELETE CASCADE,
                UNIQUE KEY unique_venue_category (venue_id, category_id)
            )
            ''')

            # Создаем таблицу связей между товарами и категориями
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS item_categories (
                item_id INTEGER,
                category_id INTEGER,
                is_primary BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (item_id, category_id),
                FOREIGN KEY (item_id) REFERENCES discounted_items(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS telegram_users (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                user_id VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255),
                last_name VARCHAR(255),
                username VARCHAR(255),
                lang VARCHAR(10) DEFAULT 'en',
                premium VARCHAR(10) DEFAULT 'false',
                pm_enabled VARCHAR(10) DEFAULT 'true',
                url_photo VARCHAR(512),
                fingerprintjs VARCHAR(512),
                ip_open_app VARCHAR(120),
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS telegram_users_locations (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                user_id VARCHAR(255),
                lat DOUBLE,
                lon DOUBLE,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES telegram_users(user_id) ON DELETE CASCADE
            )
            ''')

            # Создание таблицы для хранения рассылок Telegram
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS telegram_broadcasts (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                title VARCHAR(255),
                message TEXT NOT NULL,
                media_url VARCHAR(255),
                media_type VARCHAR(50),
                recipient_filter TEXT,
                status VARCHAR(20) DEFAULT 'draft',
                scheduled_time DATETIME,
                sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Создание таблицы для рекламных прелоадеров
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ad_preloaders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                video_url VARCHAR(512) NOT NULL,
                redirect_url VARCHAR(512) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                display_time INT DEFAULT 5,
                skip_after INT DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                views INT DEFAULT 0,
                clicks INT DEFAULT 0,
                priority INT DEFAULT 50,
                country VARCHAR(512)
            )
            ''')

            
            # Создание таблицы для proxy
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip VARCHAR(255) NOT NULL,
                port VARCHAR(255) NOT NULL,
                username VARCHAR(255) DEFAULT NULL,
                password VARCHAR(255) DEFAULT NULL,
                status VARCHAR(20) DEFAULT 'active',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (`ip`, `port`)
            )
            ''')

            # Создание таблицы для user-agents
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_agents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_agent VARCHAR(255) NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (`user_agent`)
            )
            ''')

            # Создание таблицы для настроек
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                `key` VARCHAR(255) NOT NULL,
                value TEXT,
                execution_time TIME,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (`key`)
            )
            ''')

            # Создание индексов
            cursor.execute("SHOW INDEX FROM discounted_items WHERE Key_name = 'idx_store_id'")
            if not cursor.fetchone():
                cursor.execute("CREATE INDEX idx_store_id ON discounted_items(store_id)")
            
            cursor.execute("SHOW INDEX FROM discounted_items WHERE Key_name = 'idx_discount'")
            if not cursor.fetchone():
                cursor.execute("CREATE INDEX idx_discount ON discounted_items(discount_percentage DESC)")
            
            cursor.execute("SHOW INDEX FROM discounted_items WHERE Key_name = 'idx_last_updated'")
            if not cursor.fetchone():
                cursor.execute("CREATE INDEX idx_last_updated ON discounted_items(updated_at)")

            conn.commit()
            logging.info("Таблицы успешно созданы")
        except Exception as e:
            logging.error(f"Ошибка при инициализации базы данных: {str(e)}")
            if conn.in_transaction:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def update_store(self, store_data: Dict[str, Any], update_timestamp: bool = False):
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            if update_timestamp:
                cursor.execute("""
                    INSERT INTO stores (id, name, slug, lat, lon, city, country, image_url, venue_type, currency, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        slug = VALUES(slug),
                        lat = VALUES(lat),
                        lon = VALUES(lon),
                        city = VALUES(city),
                        country = VALUES(country),
                        image_url = VALUES(image_url),
                        venue_type = VALUES(venue_type),
                        currency = VALUES(currency),
                        updated_at = VALUES(updated_at)
                """, (
                    store_data['id_venue'],
                    store_data['name'],
                    store_data['slug'],
                    store_data['lat'],
                    store_data['lon'],
                    store_data.get('city', ''),
                    store_data.get('country', ''),
                    store_data.get('image_url', ''),
                    store_data.get('venue_type', 'supermarket'),
                    store_data.get('currency', '~'),
                    datetime.now()
                ))
            else:
                cursor.execute("SELECT updated_at FROM stores WHERE id = %s", (store_data['id_venue'],))
                result = cursor.fetchone()
                if result:
                    cursor.execute("""
                        UPDATE stores 
                        SET name = %s, slug = %s, lat = %s, lon = %s, city = %s, country = %s, image_url = %s, venue_type = %s, currency = %s
                        WHERE id = %s
                    """, (
                        store_data['name'],
                        store_data['slug'],
                        store_data['lat'],
                        store_data['lon'],
                        store_data.get('city', ''),
                        store_data.get('country', ''),
                        store_data.get('image_url', ''),
                        store_data.get('venue_type', 'supermarket'),
                        store_data.get('currency', '~'),
                        store_data['id_venue']
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO stores (id, name, slug, lat, lon, city,  country, image_url, venue_type, currency)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        store_data['id_venue'],
                        store_data['name'],
                        store_data['slug'],
                        store_data['lat'],
                        store_data['lon'],
                        store_data.get('city', ''),
                        store_data.get('country', ''),
                        store_data.get('image_url', ''),
                        store_data.get('venue_type', 'supermarket'),
                        store_data.get('currency', '~')
                    ))
            conn.commit()
            logging.info(f"Информация о магазине {store_data['name']} успешно обновлена")
        except Exception as e:
            logging.error(f"Ошибка при обновлении магазина {store_data.get('name', '')}: {e}")
            conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)
    
    def mark_store_as_updated(self, store_id: str):
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE stores SET updated_at = %s WHERE id = %s", (datetime.now(), store_id))
            conn.commit()
            logging.info(f"Отметка о обновлении магазина (ID: {store_id}) установлена")
        except Exception as e:
            logging.error(f"Ошибка при обновлении времени магазина (ID: {store_id}): {e}")
            conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def update_discounted_items(self, store_id: str, items: List[Dict[str, Any]]) -> Optional[int]:
        """Обновляет скидочные товары для магазина. Возвращает количество сохраненных товаров."""
        if not items:
            return 0
        
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            
            # Получаем текущие товары со скидками для этого магазина
            cursor.execute(
                "SELECT id, id_venue FROM discounted_items WHERE store_id = %s",
                (store_id,)
            )
            existing_items = {row[1]: row[0] for row in cursor.fetchall()}
            
            # Словарь для хранения категорий по имени
            categories_by_name = {}
            
            # Получаем существующие категории для этого магазина
            cursor.execute(
                "SELECT id, name FROM categories WHERE venue_id = %s",
                (store_id,)
            )
            for cat_id, cat_name in cursor.fetchall():
                categories_by_name[cat_name] = cat_id
            
            saved_count = 0
            new_item_ids = []
            
            for item in items:
                item_venue_id = item['id_venue']
                item['store_id'] = store_id
                
                # Обработка категории
                category_name = item.get('category', '')
                
                # Удаляем категорию из основного набора полей, так как она будет храниться в отдельной таблице
                item_data = item.copy()
                
                if 'id' in item_data:
                    del item_data['id']
                
                # Удаляем поле category из данных товара, так как оно больше не хранится в таблице discounted_items
                if 'category' in item_data:
                    del item_data['category']
                
                if item_venue_id in existing_items:
                    # Обновляем существующий товар
                    item_id = existing_items[item_venue_id]
                    
                    fields = ", ".join([f"{key} = %s" for key in item_data.keys()])
                    query = f"UPDATE discounted_items SET {fields}, updated_at = NOW() WHERE id = %s"
                    
                    values = list(item_data.values())
                    values.append(item_id)
                    
                    cursor.execute(query, values)
                else:
                    # Сохраняем новый товар
                    fields = ", ".join(item_data.keys())
                    placeholders = ", ".join(["%s"] * len(item_data))
                    query = f"INSERT INTO discounted_items ({fields}) VALUES ({placeholders})"
                    
                    cursor.execute(query, list(item_data.values()))
                    item_id = cursor.lastrowid
                    new_item_ids.append(item_id)
                
                # Сохраняем категорию, если она существует и не пуста
                if category_name and category_name.strip():
                    # Получаем или создаем категорию
                    if category_name in categories_by_name:
                        category_id = categories_by_name[category_name]
                    else:
                        # Создаем новую категорию
                        category_id_str = f"{store_id}_{category_name.replace(' ', '_').lower()}"
                        
                        cursor.execute(
                            """
                            INSERT INTO categories (venue_id, category_id, name, updated_at) 
                            VALUES (%s, %s, %s, NOW())
                            ON DUPLICATE KEY UPDATE name = VALUES(name), updated_at = NOW()
                            """,
                            (store_id, category_id_str, category_name)
                        )
                        
                        if cursor.lastrowid:
                            category_id = cursor.lastrowid
                        else:
                            # Если запись уже существует, получаем её ID
                            cursor.execute(
                                "SELECT id FROM categories WHERE venue_id = %s AND category_id = %s",
                                (store_id, category_id_str)
                            )
                            category_id = cursor.fetchone()[0]
                        
                        categories_by_name[category_name] = category_id
                    
                    # Связываем товар с категорией
                    cursor.execute(
                        """
                        INSERT INTO item_categories (item_id, category_id, is_primary) 
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE is_primary = VALUES(is_primary)
                        """,
                        (item_id, category_id, True)
                    )
                
                saved_count += 1
            
            # Если в магазине нет товаров со скидками, удаляем его
            if not items:
                cursor.execute("DELETE FROM stores WHERE id = %s", (store_id,))
            
            conn.commit()
            return saved_count
        except Exception as e:
            logging.error(f"Ошибка при обновлении товаров со скидками: {str(e)}")
            if conn.in_transaction:
                conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_store(self, store_id: str) -> Optional[Dict[str, Any]]:
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM stores WHERE id = %s", (store_id,))
            return cursor.fetchone()
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_store_discounts(self, store_id: str) -> List[Dict[str, Any]]:
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM discounted_items WHERE store_id = %s ORDER BY discount_percentage DESC", (store_id,))
            return cursor.fetchall()
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_all_stores(self) -> List[Dict[str, Any]]:
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM stores ORDER BY name")
            return cursor.fetchall()
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_top_discounts(self, limit: int = 50, min_discount: float = 10.0) -> List[Dict[str, Any]]:
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT di.*, s.name as store_name, s.slug as store_slug
                FROM discounted_items di
                JOIN stores s ON di.store_id = s.id
                WHERE di.discount_percentage >= %s
                ORDER BY di.discount_percentage DESC
                LIMIT %s
            """, (min_discount, limit))
            return cursor.fetchall()
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def cleanup_old_data(self, hours: int = 24):
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            threshold = datetime.now() - timedelta(hours=hours)
            cursor.execute("DELETE FROM discounted_items WHERE updated_at < %s", (threshold,))
            items_deleted = cursor.rowcount
            cursor.execute("DELETE FROM stores WHERE updated_at < %s", (threshold,))
            stores_deleted = cursor.rowcount
            conn.commit()
            logging.info(f"Удалено {items_deleted} товаров и {stores_deleted} магазинов старше {hours} часов")
        except Exception as e:
            logging.error(f"Ошибка при очистке старых данных: {e}")
            conn.rollback()
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)
    
    async def close(self):
        self.pool.close_all()

    def get_stores_count(self) -> int:
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM stores")
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)
            
    def get_items_count(self) -> int:
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM discounted_items")
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def is_store_recently_updated(self, store_id: str, hours: int) -> bool:
        """Проверяет, был ли магазин обновлен за последние hours часов."""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT updated_at FROM stores WHERE id = %s",
                (store_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                return False
                
            last_update = result[0]
            if not last_update:
                return False
                
            # Приводим к datetime, если это не datetime
            if isinstance(last_update, str):
                last_update = datetime.fromisoformat(last_update)
                
            time_diff = datetime.now() - last_update
            return time_diff.total_seconds() < hours * 3600
            
        except Exception as e:
            logging.error(f"Ошибка при проверке времени обновления магазина: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_evenly_spaced_locations(self, min_distance_km: float = 1.5) -> List[Dict[str, Any]]:
        """
        Получает список геолокаций из таблицы telegram_users_locations, 
        которые находятся на расстоянии не менее min_distance_km друг от друга.
        
        Args:
            min_distance_km: Минимальное расстояние между точками в километрах
            
        Returns:
            Список словарей с координатами (lat, lon) на расстоянии не менее min_distance_km
        """
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            # Получаем все локации из базы
            cursor.execute("SELECT user_id, lat, lon FROM telegram_users_locations ORDER BY last_update DESC")
            all_locations = cursor.fetchall()
            
            if not all_locations:
                return []
            
            # Функция для расчета расстояния между двумя точками по формуле Гаверсинуса
            def haversine_distance(lat1, lon1, lat2, lon2):
                # Радиус Земли в километрах
                R = 6371.0
                
                # Переводим градусы в радианы
                lat1_rad = math.radians(lat1)
                lon1_rad = math.radians(lon1)
                lat2_rad = math.radians(lat2)
                lon2_rad = math.radians(lon2)
                
                # Разница в координатах
                dlon = lon2_rad - lon1_rad
                dlat = lat2_rad - lat1_rad
                
                # Формула Гаверсинуса
                a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                
                # Расстояние в километрах
                distance = R * c
                
                return distance
            
            # Отбираем равномерно распределенные точки
            selected_locations = []
            
            # Добавляем первую точку
            selected_locations.append(all_locations[0])
            
            # Проверяем каждую точку на минимальное расстояние от уже выбранных
            for location in all_locations[1:]:
                too_close = False
                
                for selected in selected_locations:
                    dist = haversine_distance(
                        float(location['lat']), float(location['lon']),
                        float(selected['lat']), float(selected['lon'])
                    )
                    
                    if dist < min_distance_km:
                        too_close = True
                        break
                
                if not too_close:
                    selected_locations.append(location)
            
            logging.info(f"Найдено {len(selected_locations)} геопозиций на расстоянии не менее {min_distance_km} км друг от друга")
            return selected_locations
            
        except Exception as e:
            logging.error(f"Ошибка при получении геопозиций: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_categories_by_store(self, store_id: str) -> List[Dict[str, Any]]:
        """Получает все категории магазина"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT c.id, c.name, c.description, COUNT(ic.item_id) AS items_count
                FROM categories c
                LEFT JOIN item_categories ic ON c.id = ic.category_id
                WHERE c.venue_id = %s
                GROUP BY c.id
                ORDER BY items_count DESC
                """,
                (store_id,)
            )
            
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка при получении категорий магазина: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)
    
    def get_items_by_category(self, category_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получает товары из определенной категории"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT di.*, s.name as store_name, s.currency
                FROM discounted_items di
                JOIN item_categories ic ON di.id = ic.item_id
                JOIN stores s ON di.store_id = s.id
                WHERE ic.category_id = %s
                ORDER BY di.discount_percentage DESC
                LIMIT %s OFFSET %s
                """,
                (category_id, limit, offset)
            )
            
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка при получении товаров по категории: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)
    
    def create_telegram_broadcast(self, recipient, language, premium, activity, registration_date, 
                                message, disable_notification, protect_content, 
                                schedule, schedule_time, media_path=None):
        """Создает запись о рассылке в базе данных"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            
            # Создаем JSON-фильтр для получателей
            recipient_filter = {
                "recipient": recipient,
                "language": language,
                "premium": premium,
                "activity": activity,
                "registration_date": registration_date,
                "disable_notification": disable_notification,
                "protect_content": protect_content
            }
            
            # Определяем тип медиа
            media_type = None
            if media_path:
                file_ext = os.path.splitext(media_path)[1].lower()
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    media_type = 'photo'
                elif file_ext in ['.mp4', '.avi', '.mov']:
                    media_type = 'video'
                elif file_ext in ['.mp3', '.wav', '.ogg']:
                    media_type = 'audio'
                else:
                    media_type = 'document'
            
            # Запрос для создания записи о рассылке
            query = """
                INSERT INTO telegram_broadcasts (
                    title, message, media_url, media_type, recipient_filter,
                    status, scheduled_time, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, NOW()
                )
            """
            
            # Формируем заголовок из первых 50 символов сообщения
            title = message[:50] + ('...' if len(message) > 50 else '')
            
            # Статус рассылки
            status = 'scheduled' if schedule else 'draft'
            
            cursor.execute(query, (
                title,
                message,
                media_path,
                media_type,
                json.dumps(recipient_filter),
                status,
                schedule_time
            ))
            
            # Получаем ID созданной рассылки
            broadcast_id = cursor.lastrowid
            
            conn.commit()
            return broadcast_id
        except Exception as e:
            logging.error(f"Ошибка при создании рассылки: {str(e)}")
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)
    
    def get_telegram_broadcast_history(self):
        """Получает историю рассылок из базы данных"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Запрос для получения истории рассылок
            query = """
                SELECT * FROM telegram_broadcasts 
                ORDER BY created_at DESC
            """
            cursor.execute(query)
            broadcasts = cursor.fetchall()
            
            return broadcasts
        except Exception as e:
            logging.error(f"Ошибка при получении истории рассылок: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)
    
    def get_scheduled_broadcasts(self):
        """Получает список запланированных рассылок, время которых уже наступило"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Получаем запланированные рассылки
            cursor.execute('''
            SELECT * FROM telegram_broadcasts
            WHERE status = 'scheduled' AND scheduled_time <= NOW()
            ORDER BY scheduled_time ASC
            ''')
            
            broadcasts = cursor.fetchall()
            
            return broadcasts
        except Exception as e:
            logging.error(f"Ошибка при получении запланированных рассылок: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_telegram_broadcast(self, broadcast_id):
        """Получает данные о конкретной рассылке"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Запрос для получения данных о рассылке
            query = """
                SELECT * FROM telegram_broadcasts 
                WHERE id = %s
            """
            cursor.execute(query, (broadcast_id,))
            broadcast = cursor.fetchone()
            
            # Распаковываем JSON-фильтр получателей
            if broadcast and broadcast['recipient_filter']:
                recipient_filter = json.loads(broadcast['recipient_filter'])
                broadcast.update(recipient_filter)
            
            return broadcast
        except Exception as e:
            logging.error(f"Ошибка при получении данных рассылки: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)
    
    def update_telegram_broadcast_status(self, broadcast_id, status, sent_count=None):
        """Обновляет статус рассылки и отметку времени отправки"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            
            if status == 'completed':
                query = """
                    UPDATE telegram_broadcasts 
                    SET status = %s, sent_at = NOW()
                    WHERE id = %s
                """
                cursor.execute(query, (status, broadcast_id))
            else:
                query = """
                    UPDATE telegram_broadcasts 
                    SET status = %s 
                    WHERE id = %s
                """
                cursor.execute(query, (status, broadcast_id))
            
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Ошибка при обновлении статуса рассылки: {str(e)}")
            if conn.in_transaction:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)
    
    def update_broadcast_progress(self, broadcast_id, progress):
        """Обновляет прогресс отправки рассылки в базе данных"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            
            # Проверяем, есть ли колонка progress в таблице telegram_broadcasts
            cursor.execute('''
            SELECT COUNT(*) as count
            FROM information_schema.columns 
            WHERE table_schema = DATABASE()
            AND table_name = 'telegram_broadcasts' 
            AND column_name = 'progress'
            ''')
            
            result = cursor.fetchone()
            column_exists = result[0] > 0
            
            # Если колонки нет, добавляем её
            if not column_exists:
                cursor.execute('''
                ALTER TABLE telegram_broadcasts
                ADD COLUMN progress INT DEFAULT 0
                ''')
                conn.commit()
            
            # Обновляем прогресс рассылки
            cursor.execute('''
            UPDATE telegram_broadcasts
            SET progress = %s
            WHERE id = %s
            ''', (progress, broadcast_id))
            
            conn.commit()
            
            return True
        except Exception as e:
            logging.error(f"Ошибка при обновлении прогресса рассылки: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)
    
    def get_telegram_users_for_broadcast(self, recipient, language, premium, activity, registration_date):
        """Получает список пользователей для рассылки на основе фильтров"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Базовый запрос
            query = """
                SELECT * FROM telegram_users 
                WHERE 1=1
            """
            params = []
            
            # Фильтр по городу
            if recipient and recipient != 'all':
                # Присоединяем таблицу локаций, если фильтруем по городу
                query = """
                    SELECT tu.* FROM telegram_users tu
                    JOIN telegram_users_locations tul ON tu.user_id = tul.user_id
                    JOIN stores s ON (
                        6371 * acos(
                            cos(radians(s.lat)) * cos(radians(tul.lat)) * 
                            cos(radians(tul.lon) - radians(s.lon)) + 
                            sin(radians(s.lat)) * sin(radians(tul.lat))
                        ) < 10
                    )
                    WHERE s.city = %s
                """
                params.append(recipient)
            
            # Фильтр по языку
            if language and language != 'all':
                if recipient and recipient != 'all':
                    query += " AND tu.lang = %s"
                else:
                    query += " AND lang = %s"
                params.append(language)

            
            
            # Фильтр по премиум статусу
            if premium == 'premium':
                if recipient and recipient != 'all':
                    query += " AND tu.premium = 'true'"
                else:
                    query += " AND premium = 'true'"
            elif premium == 'non_premium':
                if recipient and recipient != 'all':
                    query += " AND (tu.premium = 'false' OR tu.premium IS NULL)"
                else:
                    query += " AND (premium = 'false' OR premium IS NULL)"
            
            # Фильтр по активности
            if activity == 'active':
                if recipient and recipient != 'all':
                    query += " AND tu.last_update >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
                else:
                    query += " AND last_update >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
            elif activity == 'inactive':
                if recipient and recipient != 'all':
                    query += " AND tu.last_update <= DATE_SUB(NOW(), INTERVAL 30 DAY)"
                else:
                    query += " AND last_update <= DATE_SUB(NOW(), INTERVAL 30 DAY)"
            
            # Фильтр по дате регистрации
            if registration_date == 'new':
                if recipient and recipient != 'all':
                    query += " AND tu.last_update >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
                else:
                    query += " AND last_update >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
            elif registration_date == 'old':
                if recipient and recipient != 'all':
                    query += " AND tu.last_update <= DATE_SUB(NOW(), INTERVAL 30 DAY)"
                else:
                    query += " AND last_update <= DATE_SUB(NOW(), INTERVAL 30 DAY)"
            
            # Добавляем условие, что PM должен быть включен
            if recipient and recipient != 'all':
                query += " AND tu.pm_enabled = 'true'"
            else:
                query += " AND pm_enabled = 'true'"
            
            # Удаляем дубликаты, если они есть
            if recipient and recipient != 'all':
                query += " GROUP BY tu.user_id"
            
            cursor.execute(query, params)
            users = cursor.fetchall()
            
            return users
        except Exception as e:
            logging.error(f"Ошибка при получении пользователей для рассылки: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_unique_cities(self):
        """Получает список уникальных городов из таблицы stores"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT DISTINCT city FROM stores ORDER BY city"
            cursor.execute(query)
            cities = cursor.fetchall()
            return cities
        except Exception as e:
            logging.error(f"Ошибка при получении списка городов: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_unique_languages(self):
        """Получает список уникальных языков из таблицы telegram_users"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT DISTINCT lang FROM telegram_users"
            cursor.execute(query)
            languages = cursor.fetchall()
            return languages
        except Exception as e:
            logging.error(f"Ошибка при получении списка языков: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)
    
    def estimate_telegram_reach(self, recipient, language, premium, activity, registration_date):
        """Оценивает охват рассылки на основе фильтров"""
        users = self.get_telegram_users_for_broadcast(recipient, language, premium, activity, registration_date)
        return len(users)
    
    def update_user_pm_status(self, user_id, pm_enabled):
        """Обновляет статус pm_enabled пользователя в базе данных"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            
            # Обновляем статус pm_enabled пользователя
            cursor.execute('''
            UPDATE telegram_users
            SET pm_enabled = %s
            WHERE user_id = %s
            ''', ('true' if pm_enabled else 'false', user_id))
            
            conn.commit()
            
            return True
        except Exception as e:
            logging.error(f"Ошибка при обновлении статуса pm_enabled пользователя {user_id}: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    # Методы для работы с рекламными прелоадерами
    def create_ad_preloader(self, title, description, video_url, redirect_url, display_time=5, skip_after=3, priority=50, country=None):
        """Создает новую запись о рекламном прелоадере"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            
            # Обработка списка стран, если передан
            if isinstance(country, list):
                # Если передан список стран, соединяем их запятой
                country_str = ','.join(country) if country else None
            else:
                # Если передана одна страна или None
                country_str = country
                
            query = """
            INSERT INTO ad_preloaders 
            (title, description, video_url, redirect_url, display_time, skip_after, priority, is_active, country) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (title, description, video_url, redirect_url, display_time, skip_after, priority, True, country_str))
            conn.commit()
            ad_id = cursor.lastrowid
            cursor.close()
            self.pool.release_connection(conn)
            return ad_id
        except Exception as e:
            logging.error(f"Ошибка при создании рекламного прелоадера: {str(e)}")
            raise

    # Получение всех рекламных прелоадеров
    def get_all_ad_preloaders(self):
        """Возвращает список всех рекламных прелоадеров"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM ad_preloaders ORDER BY priority DESC, created_at DESC"
            cursor.execute(query)
            ads = cursor.fetchall()
            cursor.close()
            self.pool.release_connection(conn)
            return ads
        except Exception as e:
            logging.error(f"Ошибка при получении списка рекламных прелоадеров: {str(e)}")
            return []

    # Получение списка стран
    def get_all_countries(self):
        """Возвращает список всех стран"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT DISTINCT country FROM stores ORDER BY country"
            cursor.execute(query)
            countries = cursor.fetchall()
            cursor.close()
            self.pool.release_connection(conn)
            return countries
        except Exception as e:
            logging.error(f"Ошибка при получении списка стран: {str(e)}")
            return []
        
    # Получение списка городов
    def get_all_cities(self):
        """Возвращает список всех стран"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT DISTINCT city FROM stores ORDER BY city"
            cursor.execute(query)
            countries = cursor.fetchall()
            cursor.close()
            self.pool.release_connection(conn)
            return countries
        except Exception as e:
            logging.error(f"Ошибка при получении списка стран: {str(e)}")
            return []

    # Получение конкретного рекламного прелоадера
    def get_ad_preloader(self, ad_id):
        """Возвращает информацию о конкретном рекламном прелоадере"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM ad_preloaders WHERE id = %s"
            cursor.execute(query, (ad_id,))
            ad = cursor.fetchone()
            cursor.close()
            self.pool.release_connection(conn)
            return ad
        except Exception as e:
            logging.error(f"Ошибка при получении информации о рекламном прелоадере: {str(e)}")
            return None

    def update_ad_preloader(self, ad_id, title, description, video_url, redirect_url, display_time, skip_after, priority, country_id):
        """Обновляет информацию о рекламном прелоадере"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            query = """
            UPDATE ad_preloaders 
            SET title = %s, description = %s, video_url = %s, redirect_url = %s, 
                display_time = %s, skip_after = %s, priority = %s, country = %s
            WHERE id = %s
            """
            cursor.execute(query, (title, description, video_url, redirect_url, display_time, skip_after, priority, country_id, ad_id))
            conn.commit()
            cursor.close()
            self.pool.release_connection(conn)
            return True
        except Exception as e:
            logging.error(f"Ошибка при обновлении рекламного прелоадера: {str(e)}")
            raise

    def update_ad_preloader_status(self, ad_id, is_active):
        """Обновляет статус рекламного прелоадера"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            query = "UPDATE ad_preloaders SET is_active = %s WHERE id = %s"
            cursor.execute(query, (is_active, ad_id))
            conn.commit()
            cursor.close()
            self.pool.release_connection(conn)
            return True
        except Exception as e:
            logging.error(f"Ошибка при обновлении статуса рекламного прелоадера: {str(e)}")
            raise

    def delete_ad_preloader(self, ad_id):
        """Удаляет рекламный прелоадер"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            query = "DELETE FROM ad_preloaders WHERE id = %s"
            cursor.execute(query, (ad_id,))
            conn.commit()
            cursor.close()
            self.pool.release_connection(conn)
            return True
        except Exception as e:
            logging.error(f"Ошибка при удалении рекламного прелоадера: {str(e)}")
            raise

    def get_random_active_ad_preloader(self, country=None):
        """Возвращает случайный активный рекламный прелоадер с учетом приоритета и страны"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Базовый запрос с фильтрацией по статусу
            query = """
            SELECT * FROM ad_preloaders 
            WHERE is_active = TRUE 
            """
            
            params = []
            
            # Добавляем фильтрацию по стране, если страна указана
            if country:
                # Проверяем, есть ли реклама для указанной страны
                query += """
                AND (
                    country = %s 
                    OR country LIKE %s 
                    OR country LIKE %s 
                    OR country LIKE %s
                    OR country IS NULL
                    OR country = ''
                )
                """
                # Добавляем параметры для точного совпадения и совпадений в списке
                params.extend([
                    country,                  # Точное совпадение
                    f"{country},%",           # Страна в начале списка
                    f"%,{country},%",         # Страна в середине списка
                    f"%,{country}"            # Страна в конце списка
                ])
                
                # Отдаем приоритет рекламе, специфичной для данной страны
                query += """
                ORDER BY 
                    CASE 
                        WHEN country = %s THEN 3
                        WHEN country LIKE %s OR country LIKE %s OR country LIKE %s THEN 2
                        ELSE 1 
                    END DESC,
                    RAND() * priority DESC
                """
                params.extend([
                    country,
                    f"{country},%",
                    f"%,{country},%",
                    f"%,{country}"
                ])
            else:
                # Если страна не указана, выбираем рекламу без привязки к стране или с любой страной
                query += """
                ORDER BY RAND() * priority DESC
                """
            
            # Ограничиваем результат одной записью
            query += " LIMIT 1"
            
            cursor.execute(query, params if params else None)
            ad = cursor.fetchone()
            cursor.close()
            self.pool.release_connection(conn)
            return ad
        except Exception as e:
            logging.error(f"Ошибка при получении случайного рекламного прелоадера: {str(e)}")
            return None

    def increment_ad_views(self, ad_id):
        """Увеличивает счетчик просмотров рекламы"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            query = "UPDATE ad_preloaders SET views = views + 1 WHERE id = %s"
            cursor.execute(query, (ad_id,))
            conn.commit()
            cursor.close()
            self.pool.release_connection(conn)
            return True
        except Exception as e:
            logging.error(f"Ошибка при увеличении счетчика просмотров: {str(e)}")
            return False

    def increment_ad_clicks(self, ad_id):
        """Увеличивает счетчик кликов по рекламе"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            query = "UPDATE ad_preloaders SET clicks = clicks + 1 WHERE id = %s"
            cursor.execute(query, (ad_id,))
            conn.commit()
            cursor.close()
            self.pool.release_connection(conn)
            return True
        except Exception as e:
            logging.error(f"Ошибка при увеличении счетчика кликов: {str(e)}")
            return False

    # В конец класса WoltDatabase в database.py добавьте следующие методы:

    def save_proxies(self, proxies: List[str]):
        """Сохраняет список прокси в таблицу proxies, пропуская дубликаты"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            
            valid_proxies = []
            for proxy in proxies:
                parts = proxy.split(':')
                if len(parts) == 2:  # IP:PORT
                    ip, port = parts
                    username = password = None
                    valid_proxies.append((ip, port, username, password))
                elif len(parts) == 4:  # IP:PORT:USER:PASS
                    ip, port, username, password = parts
                    valid_proxies.append((ip, port, username, password))
            
            if valid_proxies:
                cursor.executemany(
                    """INSERT INTO proxies (ip, port, username, password, status) 
                    VALUES (%s, %s, %s, %s, 'active')
                    ON DUPLICATE KEY UPDATE 
                        username=VALUES(username), 
                    password=VALUES(password), 
                    status=VALUES(status),
                    updated_at=CURRENT_TIMESTAMP""",
                    valid_proxies
                )
                conn.commit()
            logging.info(f"Обработано {len(valid_proxies)} прокси (дубликаты пропущены)")
        except Exception as e:
            logging.error(f"Ошибка при сохранении прокси: {str(e)}")
            conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def delete_bad_proxies(self):
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM proxies WHERE status = 'inactive'")
            conn.commit()
            logging.info("Удалено неактивные прокси")
        except Exception as e:
            logging.error(f"Ошибка при удалении неактивных прокси: {str(e)}")
            conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def delete_all_proxies(self):
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM proxies")
            conn.commit()
            logging.info("Удалены все прокси")
        except Exception as e:
            logging.error(f"Ошибка при удалении всех прокси: {str(e)}")
            conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def delete_all_user_agents(self):
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_agents")
            conn.commit()
            logging.info("Удалены все User-Agent")
        except Exception as e:
            logging.error(f"Ошибка при удалении всех User-Agent: {str(e)}")
            conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_proxies(self) -> List[Dict[str, Any]]:
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, ip, port, username, password, status, created_at FROM proxies ORDER BY created_at DESC")
            proxies = cursor.fetchall()
            # Формируем поле proxy для совместимости с шаблоном
            for p in proxies:
                p['proxy'] = f"{p['ip']}:{p['port']}"
                if p['username'] and p['password']:
                    p['proxy'] += f":{p['username']}:{p['password']}"
            return proxies
        except Exception as e:
            logging.error(f"Ошибка при получении прокси: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_proxies_job(self) -> List[Dict[str, Any]]:
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, ip, port, username, password, status, created_at FROM proxies ORDER BY created_at DESC")
            proxies = cursor.fetchall()
            # Формируем поле proxy в нужном формате
            for p in proxies:
                if p['username'] and p['password']:
                    p['proxy'] = f"{p['username']}:{p['password']}@{p['ip']}:{p['port']}"
                else:
                    p['proxy'] = f"{p['ip']}:{p['port']}"
            return proxies
        except Exception as e:
            logging.error(f"Ошибка при получении прокси: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def save_user_agents(self, user_agents: List[str]):
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            # Очищаем текущие User-Agent
            cursor.execute("DELETE FROM user_agents")
            # Убираем дубликаты
            unique_user_agents = list(dict.fromkeys(user_agents))  # Сохраняем порядок и убираем дубликаты
            if unique_user_agents:
                cursor.executemany(
                    "INSERT IGNORE INTO user_agents (user_agent, status) VALUES (%s, 'active')",
                    [(ua,) for ua in unique_user_agents]
                )
                conn.commit()
            logging.info(f"Сохранено {len(unique_user_agents)} уникальных User-Agent")
        except Exception as e:
            logging.error(f"Ошибка при сохранении User-Agent: {str(e)}")
            conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_user_agents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает список случайных User-Agent из базы.
        :param limit: Количество случайных записей для получения (по умолчанию 100).
        :return: Список словарей с данными User-Agent.
        """
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            # Используем ORDER BY RAND() и LIMIT для получения случайных записей
            query = "SELECT user_agent, status FROM user_agents ORDER BY RAND() LIMIT %s"
            cursor.execute(query, (limit,))
            return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка при получении User-Agent: {str(e)}")
            return []
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def save_setting(self, key: str, value: str, execution_time: str = None):
        """Сохраняет настройку в таблицу settings"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO settings (`key`, value, execution_time, updated_at) 
                VALUES (%s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE value = %s, execution_time = %s, updated_at = NOW()
                """,
                (key, value, execution_time, value, execution_time)
            )
            conn.commit()
            logging.info(f"Сохранена настройка: {key} = {value}")
        except Exception as e:
            logging.error(f"Ошибка при сохранении настройки {key}: {str(e)}")
            conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_setting(self, key: str) -> Optional[str]:
        """
        Получает значение настройки по ключу.
        Возвращает значение как строку или None, если настройка не найдена.
        """
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE `key` = %s", (key,))
            result = cursor.fetchone()
            # Extract the first element of the tuple if result is not None
            return result[0] if result else None
        except Exception as e:
            logging.error(f"Ошибка при получении настройки {key}: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_last_store_update(self) -> Optional[str]:
        """
        Returns timestamp of last store update
        Returns: str timestamp or None if no updates found
        """
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(updated_at) 
                FROM stores
            """)
            result = cursor.fetchone()
            return str(result[0]) if result and result[0] else None
        except Exception as e:
            logging.error(f"Error getting last store update: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_new_users_count(self, days: int) -> int:
        """
        Counts new users registered in last N days
        Args:
            days: Number of days to look back
        Returns: Count of new users
        """
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM telegram_users 
                WHERE last_update >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (days,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logging.error(f"Error counting new users: {str(e)}")
            return 0
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_user_growth_data(self, weeks: int = None, months: int = None) -> dict:
        """
        Gets historical user growth data for charts
        Args:
            weeks: Number of weeks to look back
            months: Number of months to look back
        Returns: dict with labels and data for chart
        """
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            if weeks:
                cursor.execute("""
                    SELECT 
                        DATE_FORMAT(last_update, '%Y-%u') AS period,
                        COUNT(*) AS count
                    FROM telegram_users
                    WHERE last_update >= DATE_SUB(NOW(), INTERVAL %s WEEK)
                    GROUP BY period
                    ORDER BY period
                """, (weeks,))
            else:
                cursor.execute("""
                    SELECT 
                        DATE_FORMAT(last_update, '%Y-%m') AS period,
                        COUNT(*) AS count
                    FROM telegram_users
                    WHERE last_update >= DATE_SUB(NOW(), INTERVAL %s MONTH)
                    GROUP BY period
                    ORDER BY period
                """, (months,))
            
            results = cursor.fetchall()
            return {
                'labels': [row['period'] for row in results],
                'data': [row['count'] for row in results]
            }
        except Exception as e:
            logging.error(f"Error getting user growth data: {str(e)}")
            return {'labels': [], 'data': []}
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def get_next_store_update(self) -> Optional[str]:
        """
        Сверяем время в настройках с текущим временем
        """
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE `key` = 'execution_time'")
            result = cursor.fetchone()
            return str(result[0]) if result and result[0] else None
        except Exception as e:
            logging.error(f"Error getting next store update: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)