# telegram/database.py
import mysql.connector
from mysql.connector import pooling
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import threading
import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла в корневой директории
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Конфигурация базы данных из .env
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",  # Поддержка UTF-8
    "collation": "utf8mb4_unicode_ci"
}

logging.basicConfig(level=logging.INFO)

class ConnectionPool:
    """Пул соединений для MySQL"""
    def __init__(self, max_connections: int = 5, timeout: int = 30):
        self.max_connections = max_connections
        self.timeout = timeout
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="wolt_telegram_pool",
            pool_size=max_connections,
            **DB_CONFIG
        )
        self.lock = threading.Lock()
    
    def get_connection(self) -> mysql.connector.MySQLConnection:
        """Получить соединение из пула"""
        try:
            return self.pool.get_connection()
        except mysql.connector.Error as e:
            logging.error(f"Ошибка получения соединения из пула: {e}")
            raise
    
    def release_connection(self, conn: mysql.connector.MySQLConnection):
        """Освободить соединение обратно в пул"""
        if conn and conn.is_connected():
            conn.close()
    
    def close_all(self):
        """Закрыть все соединения в пуле"""
        try:
            self.pool._remove_connections()
        except Exception as e:
            logging.error(f"Ошибка закрытия пула соединений: {e}")

class WoltTelegramDatabase:
    def __init__(self, pool_size: int = 5):
        self.pool = ConnectionPool(max_connections=pool_size)
        self._init_db()

    def _init_db(self):
        """Инициализация таблиц базы данных, если они не существуют"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            # Создание таблиц с поддержкой UTF-8
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stores (
                    id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255),
                    slug VARCHAR(255),
                    lat DOUBLE,
                    lon DOUBLE,
                    city VARCHAR(100),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS discounted_items (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    id_venue VARCHAR(255),
                    store_id VARCHAR(255),
                    name VARCHAR(255),
                    description TEXT,
                    category VARCHAR(100),
                    image_url VARCHAR(512),
                    current_price DOUBLE,
                    original_price DOUBLE,
                    base_price DOUBLE,
                    discount_percentage DOUBLE,
                    currency VARCHAR(10) DEFAULT 'GEL',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telegram_users (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    user_id VARCHAR(255) UNIQUE,
                    name VARCHAR(255),
                    last_name VARCHAR(255),
                    username VARCHAR(255),
                    lang VARCHAR(10) DEFAULT 'en',
                    premium VARCHAR(10) DEFAULT 'false',
                    pm_enabled VARCHAR(10) DEFAULT 'true',
                    url_photo VARCHAR(512),
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telegram_users_locations (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    user_id VARCHAR(255),
                    lat DOUBLE,
                    lon DOUBLE,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES telegram_users(user_id) ON DELETE CASCADE
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
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
            logging.info("Все таблицы базы данных инициализированы")
        except Exception as e:
            logging.error(f"Ошибка при инициализации базы данных: {e}")
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def update_telegram_user(self, user_data: Dict[str, Any]):
        """Обновление или вставка данных пользователя Telegram"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO telegram_users (
                    user_id, name, last_name, username, lang, premium, pm_enabled, url_photo, last_update
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    last_name = VALUES(last_name),
                    username = VALUES(username),
                    lang = VALUES(lang),
                    premium = VALUES(premium),
                    pm_enabled = VALUES(pm_enabled),
                    url_photo = VALUES(url_photo),
                    last_update = VALUES(last_update)
            """, (
                user_data['user_id'],
                user_data.get('name'),
                user_data.get('last_name'),
                user_data.get('username'),
                user_data.get('lang', 'en'),
                user_data.get('premium', 'false'),
                user_data.get('pm_enabled', 'true'),
                user_data.get('url_photo'),
                datetime.now()
            ))
            conn.commit()
            logging.info(f"Пользователь {user_data['user_id']} обновлён")
        except Exception as e:
            logging.error(f"Ошибка при обновлении пользователя Telegram: {e}")
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)

    def update_user_location(self, user_id: str, lat: float, lon: float):
        """Обновление местоположения пользователя"""
        conn = self.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM telegram_users WHERE user_id = %s", (user_id,))
            if cursor.fetchone()[0] == 0:
                raise ValueError(f"Пользователь с user_id {user_id} не найден")
            cursor.execute("""
                INSERT INTO telegram_users_locations (user_id, lat, lon, last_update)
                VALUES (%s, %s, %s, %s)
            """, (user_id, lat, lon, datetime.now()))
            conn.commit()
            logging.info(f"Местоположение пользователя {user_id} добавлено")
        except Exception as e:
            logging.error(f"Ошибка при обновлении местоположения: {e}")
            if conn.in_transaction:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            self.pool.release_connection(conn)