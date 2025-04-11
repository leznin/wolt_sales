from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import sys
import json
import math
import logging
import threading
import urllib
import hmac
import hashlib
import subprocess
import re
from datetime import datetime
import tempfile
from dotenv import load_dotenv
from telegram.user import webhook

# Глобальная переменная для хранения последнего прогресса выполнения
last_progress = {
    'progress': 0,
    'progress_text': 'Ожидание запуска...',
    'proxy_stats': {}
}

# Временный файл для записи вывода процесса
PROGRESS_FILE = os.path.join(tempfile.gettempdir(), 'wolt_progress.txt')

# Импорт модуля интеграции админ-панели
from app.admin_integration import integrate_admin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Путь к файлу .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(dotenv_path=env_path)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
logger.info(f"Bot token: {TELEGRAM_TOKEN}")

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from database import WoltDatabase

current_dir = os.path.dirname(os.path.abspath(__file__))
static_folder = os.path.join(current_dir, 'build')
public_folder = os.path.join(current_dir, 'public')

# Динамические пути к папкам
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PHOTOS_DIR = os.path.join(BASE_DIR, 'app', 'telegram', 'photos')
PUBLIC_IMAGES_DIR = os.path.join(BASE_DIR, 'app', 'public', 'images')

app = Flask(__name__, static_folder=static_folder, static_url_path='/')
CORS(app)

# Интеграция админ-панели
app = integrate_admin(app)

db_local = threading.local()

def get_db():
    """Get a thread-local database connection"""
    if not hasattr(db_local, 'db'):
        try:
            # Инициализация WoltDatabase для MySQL (без db_path, так как используется .env)
            db_local.db = WoltDatabase()
            logger.info(f"Database initialized for thread {threading.get_ident()}")
        except Exception as e:
            logger.error(f"Error initializing database for thread {threading.get_ident()}: {e}")
            db_local.db = None
    return db_local.db

@app.route('/api/stores', methods=['GET'])
def get_stores_with_discounts():
    """Get all stores that have discounted items"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        venue_type = request.args.get('venue_type', default=None)
        stores = db.get_all_stores()
        stores_with_discounts = []
        
        for store in stores:
            # Filter by venue_type if specified
            if venue_type and store.get('venue_type') != venue_type:
                continue
                
            discounts = db.get_store_discounts(store['id'])
            if discounts:  # Only include stores with discounts
                store['discount_count'] = len(discounts)
                # Calculate average discount percentage
                if discounts:
                    avg_discount = sum(item['discount_percentage'] for item in discounts) / len(discounts)
                    store['avg_discount'] = round(avg_discount, 1)
                else:
                    store['avg_discount'] = 0
                stores_with_discounts.append(store)
        
        logger.info(f"Retrieved {len(stores_with_discounts)} stores with discounts" + 
                   (f" for venue_type: {venue_type}" if venue_type else ""))
        return jsonify(stores_with_discounts)
    except Exception as e:
        logger.error(f"Error getting stores with discounts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/venue-types', methods=['GET'])
def get_venue_types():
    """Get all available venue types"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        # Используем подключение из пула через WoltDatabase
        conn = db.pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT venue_type FROM stores WHERE venue_type IS NOT NULL")
        venue_types = [row[0] for row in cursor.fetchall()]
        conn.commit()
        logger.info(f"Retrieved {len(venue_types)} venue types")
        return jsonify(venue_types)
    except Exception as e:
        logger.error(f"Error getting venue types: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            db.pool.release_connection(conn)

@app.route('/api/store/<store_id>/discounts', methods=['GET'])
def get_store_discounts(store_id):
    """Get all discounted items for a specific store"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        store = db.get_store(store_id)
        if not store:
            logger.warning(f"Store not found: {store_id}")
            return jsonify({"error": "Store not found"}), 404
        
        discounts = db.get_store_discounts(store_id)
        logger.info(f"Retrieved {len(discounts)} discounts for store {store_id}")
        return jsonify({
            "store": store,
            "discounts": discounts
        })
    except Exception as e:
        logger.error(f"Error getting discounts for store {store_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/top-discounts', methods=['GET'])
def get_top_discounts():
    """Get top discounted items across all stores"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        limit = request.args.get('limit', default=50, type=int)
        min_discount = request.args.get('min_discount', default=10.0, type=float)
        
        discounts = db.get_top_discounts(limit=limit, min_discount=min_discount)
        logger.info(f"Retrieved {len(discounts)} top discounts")
        return jsonify(discounts)
    except Exception as e:
        logger.error(f"Error getting top discounts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/user-locations/<user_id>', methods=['GET'])
def get_user_locations(user_id):
    """Get all saved locations for a specific user"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        # Используем подключение из пула через WoltDatabase
        conn = db.pool.get_connection()
        cursor = None
        try:
            # Проверяем, существует ли столбец name в таблице
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count FROM information_schema.columns 
                WHERE table_name = 'telegram_users_locations' AND column_name = 'name'
            """)
            column_exists = cursor.fetchone()[0] > 0
            
            # Если столбец не существует, добавляем его
            if not column_exists:
                cursor.execute("""
                    ALTER TABLE telegram_users_locations
                    ADD COLUMN name VARCHAR(255) DEFAULT NULL
                """)
                conn.commit()
                logger.info("Added 'name' column to telegram_users_locations table")
            
            # Получаем геопозиции пользователя
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, user_id, lat, lon, name, last_update 
                FROM telegram_users_locations 
                WHERE user_id = %s
                ORDER BY last_update DESC
            """, (user_id,))
            locations = cursor.fetchall()
            logger.info(f"Retrieved {len(locations)} locations for user {user_id}")
            return jsonify(locations)
        except Exception as e:
            logger.error(f"Error getting locations for user {user_id}: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            db.pool.release_connection(conn)
    except Exception as e:
        logger.error(f"Error in get_user_locations: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/user-locations/<location_id>', methods=['PUT'])
def update_user_location(location_id):
    """Update a specific user location by ID"""
    try:
        data = request.json
        name = data.get('name')
        
        if not name:
            return jsonify({"error": "Name is required"}), 400
            
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        # Используем подключение из пула через WoltDatabase
        conn = db.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE telegram_users_locations 
                SET name = %s
                WHERE id = %s
            """, (name, location_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Updated location name for ID {location_id} to '{name}'")
                return jsonify({"success": True, "message": "Location name updated successfully"})
            else:
                logger.warning(f"Location with ID {location_id} not found")
                return jsonify({"error": "Location not found"}), 404
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating location {location_id}: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            db.pool.release_connection(conn)
    except Exception as e:
        logger.error(f"Error in update_user_location: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/store/<store_id>/categories', methods=['GET'])
def get_store_categories(store_id):
    """Get all categories of discounted items for a specific store"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        store = db.get_store(store_id)
        if not store:
            logger.warning(f"Store not found: {store_id}")
            return jsonify({"error": "Store not found"}), 404
        
        # Получаем категории из новой структуры базы данных
        categories = db.get_categories_by_store(store_id)
        
        logger.info(f"Retrieved {len(categories)} categories for store {store_id}")
        return jsonify(categories)
    except Exception as e:
        logger.error(f"Error getting categories for store {store_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/user-locations/<location_id>', methods=['DELETE'])
def delete_user_location(location_id):
    """Delete a specific user location by ID"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        # Используем подключение из пула через WoltDatabase
        conn = db.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM telegram_users_locations 
                WHERE id = %s
            """, (location_id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Deleted location with ID {location_id}")
                return jsonify({"success": True, "message": "Location deleted successfully"})
            else:
                logger.warning(f"Location with ID {location_id} not found")
                return jsonify({"error": "Location not found"}), 404
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting location {location_id}: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            db.pool.release_connection(conn)
    except Exception as e:
        logger.error(f"Error in delete_user_location: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/category/<int:category_id>/items', methods=['GET'])
def get_category_items(category_id):
    """Get all items in a specific category"""
    try:
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        items = db.get_items_by_category(category_id, limit, offset)
        return jsonify(items)
    except Exception as e:
        logger.error(f"Error getting items for category {category_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/user-last-location/<int:user_id>', methods=['GET'])
def get_user_last_location(user_id):
    """Get the last location for a specific user"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        # Используем подключение из пула через WoltDatabase
        conn = db.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Получаем последнюю локацию пользователя
            cursor.execute(
                """
                SELECT lat, lon, name, last_update 
                FROM telegram_users_locations 
                WHERE user_id = %s 
                ORDER BY last_update DESC 
                LIMIT 1
                """, 
                (user_id,)
            )
            
            location = cursor.fetchone()
            
            if location:
                logger.info(f"Retrieved last location for user {user_id}: {location}")
                return jsonify(location)
            else:
                logger.info(f"No location found for user {user_id}")
                return jsonify(None)
                
        except Exception as e:
            logger.error(f"Error getting user last location: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            db.pool.release_connection(conn)
    except Exception as e:
        logger.error(f"Error in get_user_last_location: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stores-by-location', methods=['GET'])
def get_stores_by_location():
    """Get stores with discounts within a certain radius of given coordinates"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        # Получаем параметры запроса
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius_km = request.args.get('radius', default=3.0, type=float)
        venue_type = request.args.get('venue_type', default=None)
        
        logger.info(f"Получен запрос на магазины рядом с локацией: lat={lat}, lon={lon}, radius={radius_km}, venue_type={venue_type}")
        
        if lat is None or lon is None:
            logger.error("Ошибка: не указаны координаты lat или lon")
            return jsonify({"error": "Latitude and longitude are required"}), 400
            
        # Получаем все магазины
        stores = db.get_all_stores()
        logger.info(f"Всего найдено магазинов: {len(stores)}")
        
        stores_with_discounts = []
        
        # Импортируем функцию расчета расстояния
        from math import radians, sin, cos, sqrt, atan2
        
        # Определяем функцию расчета расстояния локально
        def haversine_distance(lat1, lon1, lat2, lon2):
            # Радиус Земли в километрах
            R = 6371.0
            
            # Переводим градусы в радианы
            lat1_rad = radians(float(lat1))
            lon1_rad = radians(float(lon1))
            lat2_rad = radians(float(lat2))
            lon2_rad = radians(float(lon2))
            
            # Разница в координатах
            dlon = lon2_rad - lon1_rad
            dlat = lat2_rad - lat1_rad
            
            # Формула Гаверсинуса
            a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            
            # Расстояние в километрах
            distance = R * c
            
            return distance
        
        for store in stores:
            # Фильтруем по типу заведения, если указан
            if venue_type and store.get('venue_type') != venue_type:
                continue
                
            # Вычисляем расстояние от заданной точки до магазина
            store_lat = store.get('lat')
            store_lon = store.get('lon')
            
            if store_lat is None or store_lon is None:
                continue
                
            # Используем локальную функцию haversine_distance вместо вызова через класс
            distance = haversine_distance(lat, lon, store_lat, store_lon)
            logger.debug(f"Магазин {store['name']}: расстояние = {distance} км")
            
            # Проверяем, находится ли магазин в заданном радиусе
            if distance <= radius_km:
                # Проверяем, есть ли в магазине товары со скидками
                discounts = db.get_store_discounts(store['id'])
                if discounts:  # Только магазины со скидками
                    store['discount_count'] = len(discounts)
                    store['distance'] = round(distance, 2)  # Округляем до 2 знаков после запятой
                    
                    # Вычисляем среднюю скидку
                    if discounts:
                        avg_discount = sum(item['discount_percentage'] for item in discounts) / len(discounts)
                        store['avg_discount'] = round(avg_discount, 1)
                    else:
                        store['avg_discount'] = 0
                        
                    stores_with_discounts.append(store)
        
        # Сортируем магазины по расстоянию (ближайшие сначала)
        stores_with_discounts.sort(key=lambda x: x.get('distance', float('inf')))
        
        logger.info(f"Найдено {len(stores_with_discounts)} магазинов в радиусе {radius_km}км от ({lat}, {lon})" +
                   (f" для типа: {venue_type}" if venue_type else ""))
                   
        return jsonify(stores_with_discounts)
    except Exception as e:
        logger.error(f"Ошибка при получении магазинов по локации: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/search-products', methods=['GET'])
def search_products():
    """Поиск товаров по названию во всех магазинах"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        # Получаем параметры поиска
        search_term = request.args.get('query', '')
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', default=3.0, type=float)
        
        if not search_term or len(search_term.strip()) < 2:
            return jsonify([])
        
        conn = db.pool.get_connection()
        cursor = None
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Базовый запрос для поиска товаров по названию
            query = """
                SELECT 
                    di.id, di.id_venue, di.store_id, di.name, 
                    di.description, di.image_url, di.current_price, 
                    di.original_price, di.discount_percentage,
                    s.name as store_name, s.slug as store_slug, 
                    s.city as store_city, s.lat, s.lon, s.currency
                FROM discounted_items di
                JOIN stores s ON di.store_id = s.id
                WHERE di.name LIKE %s
            """
            
            # Если указаны координаты, фильтруем по расстоянию
            if lat is not None and lon is not None:
                # Добавляем фильтр по расстоянию с формулой Гаверсинуса
                query += """
                    AND (
                        6371 * acos(
                            cos(radians(%s)) * cos(radians(s.lat)) * 
                            cos(radians(s.lon) - radians(%s)) + 
                            sin(radians(%s)) * sin(radians(s.lat))
                        )
                    ) <= %s
                """
                cursor.execute(
                    query, 
                    (f"%{search_term}%", lat, lon, lat, radius)
                )
            else:
                cursor.execute(query, (f"%{search_term}%",))
            
            results = cursor.fetchall()
            
            # Если указаны координаты, добавляем информацию о расстоянии для каждого товара
            if lat is not None and lon is not None:
                for product in results:
                    if product['lat'] and product['lon']:
                        # Расчет расстояния по формуле Гаверсинуса
                        product_lat = float(product['lat'])
                        product_lon = float(product['lon'])
                        
                        # Радиус Земли в километрах
                        R = 6371.0
                        
                        # Переводим градусы в радианы
                        lat1_rad = math.radians(lat)
                        lon1_rad = math.radians(lon)
                        lat2_rad = math.radians(product_lat)
                        lon2_rad = math.radians(product_lon)
                        
                        # Разница в координатах
                        dlon = lon2_rad - lon1_rad
                        dlat = lat2_rad - lat1_rad
                        
                        # Формула Гаверсинуса
                        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                        
                        # Расстояние в километрах
                        distance = R * c
                        
                        product['distance'] = distance
            
            # Сортируем результаты по цене (от низкой к высокой)
            results.sort(key=lambda x: float(x.get('current_price', 999999)))
            
            logger.info(f"Найдено {len(results)} товаров по запросу: {search_term}")
            return jsonify(results)
            
        except Exception as e:
            logger.error(f"Ошибка при поиске товаров: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            if 'conn' in locals():
                db.pool.release_connection(conn)
    except Exception as e:
        logger.error(f"Ошибка при поиске товаров: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/user-countries/<user_id>', methods=['GET'])
def get_user_countries(user_id):
    """Get the countries of stores that a user is tracking based on their saved locations"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
            
        # Получаем локации пользователя
        conn = db.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Получаем все сохраненные локации пользователя
            cursor.execute(
                """
                SELECT lat, lon
                FROM telegram_users_locations 
                WHERE user_id = %s 
                ORDER BY last_update DESC
                """, 
                (user_id,)
            )
            
            locations = cursor.fetchall()
            
            if not locations:
                logger.info(f"No locations found for user {user_id}")
                return jsonify([])
                
            # Получаем страны магазинов в радиусе от локаций пользователя
            countries = set()
            
            # Импортируем функцию расчета расстояния
            from math import radians, sin, cos, sqrt, atan2
            
            # Определяем функцию расчета расстояния локально
            def haversine_distance(lat1, lon1, lat2, lon2):
                # Радиус Земли в километрах
                R = 6371.0
                
                # Переводим градусы в радианы
                lat1_rad = radians(float(lat1))
                lon1_rad = radians(float(lon1))
                lat2_rad = radians(float(lat2))
                lon2_rad = radians(float(lon2))
                
                # Разница в координатах
                dlon = lon2_rad - lon1_rad
                dlat = lat2_rad - lat1_rad
                
                # Формула Гаверсинуса
                a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                
                # Расстояние в километрах
                distance = R * c
                
                return distance
            
            # Получаем все магазины
            stores = db.get_all_stores()
            
            # Определяем радиус поиска (км)
            radius = 10.0
            
            # Проверяем каждую локацию пользователя
            for location in locations:
                for store in stores:
                    if not store.get('lat') or not store.get('lon') or not store.get('country'):
                        continue
                        
                    # Вычисляем расстояние от локации до магазина
                    distance = haversine_distance(
                        location['lat'], location['lon'],
                        store['lat'], store['lon']
                    )
                    
                    # Если магазин находится в радиусе поиска, добавляем его страну
                    if distance <= radius:
                        countries.add(store['country'])
            
            logger.info(f"Found {len(countries)} countries for user {user_id}: {', '.join(countries)}")
            return jsonify(list(countries))
                
        except Exception as e:
            logger.error(f"Error getting countries for user {user_id}: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor:
                cursor.close()
            db.pool.release_connection(conn)
    except Exception as e:
        logger.error(f"Error in get_user_countries: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/progress', methods=['GET'])
def get_progress():
    """Get the current progress of the main.py script"""
    try:
        # Проверяем, запущен ли процесс main.py
        process_running = False
        try:
            result = subprocess.run(['pgrep', '-f', 'python.*main\.py'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   text=True)
            process_pids = result.stdout.strip().split('\n')
            process_running = len(process_pids) > 0 and process_pids[0] != ''
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса процесса: {e}")
        
        # Пытаемся прочитать файл с прогрессом
        stats_path = os.path.join(parent_dir, "processing_stats.json")
        
        if os.path.exists(stats_path):
            try:
                with open(stats_path, "r") as f:
                    stats = json.load(f)
                    
                    # Получаем основные данные статистики
                    processed_stores = stats.get("processed_stores", 0)
                    total_stores = stats.get("total_stores", 0)
                    processed_items = stats.get("processed_items", 0)
                    discounted_items = stats.get("discounted_items", 0)
                    saved_items = stats.get("saved_items", 0)
                    last_update = stats.get("last_update", "")
                    
                    # Вычисляем прогресс
                    progress = 0
                    if total_stores > 0:
                        progress = min(round((processed_stores / total_stores) * 100, 1), 100)
                    
                    # Формируем текст прогресса
                    if process_running:
                        progress_text = f"Выполняется: обработано {processed_stores} из {total_stores} магазинов"
                        if discounted_items > 0:
                            progress_text += f", найдено {discounted_items} товаров со скидками"
                    else:
                        if processed_stores > 0:
                            if processed_stores >= total_stores:
                                progress_text = f"Процесс завершен. Обработано {processed_stores} магазинов, найдено {discounted_items} товаров со скидками"
                            else:
                                progress_text = f"Процесс остановлен. Обработано {processed_stores} из {total_stores} магазинов"
                        else:
                            progress_text = "Процесс не запущен"
                    
                    # Получаем статистику использования прокси
                    proxy_stats = stats.get("proxy_stats", {})
                    
                    return jsonify({
                        'progress': progress,
                        'progress_text': progress_text,
                        'processed_stores': processed_stores,
                        'total_stores': total_stores,
                        'processed_items': processed_items,
                        'discounted_items': discounted_items,
                        'saved_items': saved_items,
                        'last_update': last_update,
                        'process_running': process_running,
                        'proxy_stats': proxy_stats
                    }), 200
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка при чтении файла processing_stats.json: {e}")
        
        # Если нет файла с прогрессом или произошла ошибка
        return jsonify({
            'progress': 0,
            'progress_text': 'Выполняется запуск процесса...' if process_running else 'Процесс не запущен',
            'processed_stores': 0,
            'total_stores': 0,
            'processed_items': 0,
            'discounted_items': 0,
            'saved_items': 0,
            'last_update': '',
            'process_running': process_running,
            'proxy_stats': {}
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка при получении прогресса: {e}")
        return jsonify({
            'progress': 0,
            'progress_text': f'Ошибка: {str(e)}',
            'proxy_stats': {},
            'process_running': False
        }), 500

@app.route('/start-main', methods=['POST'])
def start_main():
    try:
        # Используем абсолютный путь к файлу main.py
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        main_path = os.path.join(base_dir, 'main.py')
        
        # Проверяем существование файла
        if not os.path.exists(main_path):
            logger.error(f"Файл main.py не найден по пути: {main_path}")
            return jsonify({'error': f'Файл не найден: {main_path}'}), 404
        
        # Обновляем глобальную переменную с прогрессом
        global last_progress
        last_progress = {
            'progress': 0,
            'progress_text': 'Запуск скрипта...',
            'proxy_stats': {}
        }
        
        # Создаем файл лога, если он не существует
        log_path = os.path.join(base_dir, 'wolt_parser.log')
        with open(log_path, 'w') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] Запуск скрипта main.py\n")
        
        # Запускаем процесс в фоновом режиме
        try:
            # Используем python3 для запуска скрипта
            process = subprocess.Popen(
                ['python3', '-u', main_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                cwd=base_dir  # Устанавливаем рабочую директорию
            )
            
            # Создаем поток для записи вывода в файл и обновления прогресса
            def log_output():
                with open(log_path, 'a') as log_file:
                    for line in process.stdout:
                        try:
                            # Записываем строку в лог
                            log_file.write(line)
                            log_file.flush()
                            
                            # Обновляем глобальную переменную с прогрессом, если строка содержит информацию о прогрессе
                            if 'Прогресс:' in line:
                                # Извлекаем процент выполнения
                                progress_percentage = 0
                                match = re.search(r'(\d+\.\d+)%', line)
                                if match:
                                    progress_percentage = float(match.group(1))
                                
                                # Извлекаем статистику прокси
                                proxy_stats = {}
                                proxy_match = re.search(r'Прокси: ([\d:, ]+)', line)
                                if proxy_match:
                                    proxy_text = proxy_match.group(1)
                                    proxy_pairs = proxy_text.split(', ')
                                    for pair in proxy_pairs:
                                        if ':' in pair:
                                            proxy_id, count = pair.split(':')
                                            proxy_stats[proxy_id.strip()] = int(count.strip())
                                
                                # Обновляем глобальную переменную
                                global last_progress
                                last_progress = {
                                    'progress': progress_percentage,
                                    'progress_text': line.strip(),
                                    'proxy_stats': proxy_stats
                                }
                        except Exception as e:
                            # Логируем ошибку, но не останавливаем поток
                            logger.error(f"Ошибка при обработке вывода скрипта: {e}")
                            continue
            
            # Запускаем поток для записи вывода
            thread = threading.Thread(target=log_output, daemon=True)
            thread.start()
            
            # Записываем информацию о запуске в файл
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            start_info = {
                'last_start': timestamp,
                'status': 'running',
                'pid': process.pid
            }
            
            # Путь к файлу с информацией о запусках
            start_info_path = os.path.join(base_dir, 'app', 'start_info.json')
            
            with open(start_info_path, 'w') as f:
                json.dump(start_info, f)
            
            logger.info(f"Скрипт main.py успешно запущен с PID {process.pid}")
            return jsonify({'message': 'Скрипт main.py успешно запущен!', 'pid': process.pid}), 200
            
        except subprocess.SubprocessError as e:
            logger.error(f"Ошибка при запуске подпроцесса: {e}")
            return jsonify({'error': f'Ошибка при запуске скрипта: {str(e)}'}), 500
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Неожиданная ошибка при запуске main.py: {str(e)}\n{error_details}")
        return jsonify({'error': str(e)}), 500

@app.route('/stop-main', methods=['POST'])
def stop_main():
    """API-эндпоинт для остановки выполнения процесса main.py"""
    try:
        import subprocess
        import json
        import os
        import signal
        from datetime import datetime
        
        # Проверяем, запущен ли процесс main.py
        result = subprocess.run(['pgrep', '-f', 'python.*main\.py'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        
        process_pids = result.stdout.strip().split('\n')
        pid_list = [pid for pid in process_pids if pid]
        
        if not pid_list:
            return jsonify({
                'success': False, 
                'message': 'Процесс не запущен или не может быть найден'
            }), 404
        
        # Завершаем процесс
        for pid in pid_list:
            try:
                # Сначала пробуем завершить процесс корректно (SIGTERM)
                os.kill(int(pid), signal.SIGTERM)
                logger.info(f"Отправлен сигнал SIGTERM процессу с PID {pid}")
            except Exception as e:
                logger.error(f"Ошибка при завершении процесса {pid}: {e}")
                # Если не удалось завершить корректно, убиваем процесс (SIGKILL)
                try:
                    os.kill(int(pid), signal.SIGKILL)
                    logger.info(f"Отправлен сигнал SIGKILL процессу с PID {pid}")
                except Exception as kill_error:
                    logger.error(f"Ошибка при принудительном завершении процесса {pid}: {kill_error}")
                    return jsonify({
                        'success': False, 
                        'message': f'Не удалось завершить процесс: {str(kill_error)}'
                    }), 500
        
        # Обновляем информацию о статусе процесса
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        stats_path = os.path.join(base_dir, "processing_stats.json")
        
        if os.path.exists(stats_path):
            try:
                with open(stats_path, "r") as f:
                    stats = json.load(f)
                
                # Сохраняем данные о прокси
                proxy_stats = stats.get("proxy_stats", {})
                
                # Сбрасываем все счетчики на 0
                stats = {
                    "processed_stores": 0,
                    "total_stores": 0,
                    "processed_items": 0,
                    "discounted_items": 0,
                    "saved_items": 0,
                    "failed_stores": 0,
                    "stores_with_errors": [],
                    "proxy_stats": proxy_stats,
                    "manually_stopped": True,
                    "stop_time": datetime.now().isoformat(),
                    "last_update": datetime.now().isoformat()
                }
                
                with open(stats_path, "w") as f:
                    json.dump(stats, f)
                
                logger.info("Счетчики статистики сброшены на 0 после остановки процесса")
            except Exception as e:
                logger.error(f"Ошибка при обновлении файла статистики: {e}")
        
        # Запись в лог-файл
        log_path = os.path.join(base_dir, "wolt_parser.log")
        try:
            with open(log_path, 'a') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] Процесс остановлен вручную через административный интерфейс. Счетчики сброшены на 0.\n")
        except Exception as e:
            logger.error(f"Ошибка при записи в лог-файл: {e}")
        
        return jsonify({
            'success': True, 
            'message': f'Процесс успешно остановлен. Завершено {len(pid_list)} процессов. Счетчики сброшены на 0.'
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Неожиданная ошибка при остановке процесса: {str(e)}\n{error_details}")
        return jsonify({
            'success': False, 
            'message': f'Ошибка при остановке процесса: {str(e)}'
        }), 500

# Serve static files from the public directory during development
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(public_folder, 'favicon.ico')

@app.route('/logo192.png')
def logo192():
    return send_from_directory(public_folder, 'logo192.png')

@app.route('/logo512.png')
def logo512():
    return send_from_directory(public_folder, 'logo512.png')

@app.route('/manifest.json')
def manifest():
    return send_from_directory(public_folder, 'manifest.json')


@app.route('/store/<path:store_id>')
def serve_store_page(store_id):
    return app.send_static_file('index.html')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return app.send_static_file(path)
    else:
        return app.send_static_file('index.html')

app.route('/webhook', methods=['POST'])(webhook)

# Маршруты для раздачи статических файлов
@app.route('/telegram/photos/<path:filename>')
def serve_user_photo(filename):
    full_path = os.path.join(PHOTOS_DIR, filename)
    logger.info(f"Serving photo: {full_path}, exists: {os.path.exists(full_path)}")
    if not os.path.exists(full_path):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(PHOTOS_DIR, filename)

@app.route('/public/images/<path:filename>')
def serve_public_image(filename):
    return send_from_directory(PUBLIC_IMAGES_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)