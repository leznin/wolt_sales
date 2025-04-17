# handlers.py
from telegram import Update
from telegram.ext import ContextTypes
from .messages import get_text
from .keyboards import get_main_keyboard, get_back_keyboard, get_location_received_keyboard
from .database import WoltTelegramDatabase
from .get_photo import save_user_avatar
import logging
from flask import jsonify

db = WoltTelegramDatabase()

def start_command(data):
    try:
        # Извлекаем информацию о пользователе из данных
        user_info = data.get('message', {}).get('from', {})
        user_id = user_info.get('id')
        first_name = user_info.get('first_name', '')
        last_name = user_info.get('last_name', '')
        username = user_info.get('username', '')
        lang = user_info.get('language_code', 'en')
        is_premium = user_info.get('is_premium', False)

        # получаем фото
        photo = save_user_avatar(data)
        
        # Сохраняем данные пользователя в базу
        conn = db.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            
            # Проверяем, существует ли пользователь
            cursor.execute("""
                SELECT user_id FROM telegram_users WHERE user_id = %s
            """, (str(user_id),))
            
            user_exists = cursor.fetchone()
            
            if user_exists:
                # Если пользователь существует, обновляем его данные
                cursor.execute("""
                    UPDATE telegram_users SET
                        name = %s,
                        last_name = %s,
                        username = %s,
                        lang = %s,
                        premium = %s,
                        last_update = CURRENT_TIMESTAMP,
                        url_photo = %s
                    WHERE user_id = %s
                """, (
                    first_name,
                    last_name,
                    username,
                    lang,
                    str(is_premium).lower(),
                    photo,
                    str(user_id)
                ))
            else:
                # Если пользователь не существует, вставляем новую запись
                cursor.execute("""
                    INSERT INTO telegram_users (
                        user_id, name, last_name, username, lang, premium, url_photo
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(user_id),
                    first_name,
                    last_name,
                    username,
                    lang,
                    str(is_premium).lower(),
                    photo
                ))
            
            conn.commit()
            logging.info(f"Пользователь {user_id} сохранен в базе данных")
        except Exception as e:
            logging.error(f"Ошибка при сохранении пользователя: {e}")
            if conn.in_transaction:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            db.pool.release_connection(conn)
        
        # Получаем клавиатуру в формате JSON
        keyboard = get_main_keyboard(lang)
        keyboard_dict = keyboard.to_dict() if hasattr(keyboard, 'to_dict') else {
            'inline_keyboard': [[{'text': btn.text, 'callback_data': btn.callback_data} for btn in row] for row in keyboard.inline_keyboard]
        }
        
        # Возвращаем ответ для webhook
        return jsonify({
            "method": "sendMessage",
            "chat_id": data.get('message', {}).get('chat', {}).get('id'),
            "text": get_text('start', lang, user=first_name),
            "reply_markup": keyboard_dict
        }), 200
    except Exception as e:
        logging.error(f"Ошибка в start_command: {e}")
        return jsonify({"error": str(e)}), 500


def save_user_avatar(data, save_folder: str = 'telegram_bot/photos') -> str:
    """
    Получает и сохраняет аватарку пользователя с использованием requests.
    
    Аргументы:
        data: данные из webhook
        save_folder: папка для сохранения (по умолчанию 'photos')
    
    Возвращает:
        str: имя файла или None, если фото не удалось получить
    """
    import os
    import requests
    from dotenv import load_dotenv
    
    # Загружаем переменные окружения из .env файла с правильным путем
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    load_dotenv(env_path)
    
    # Создаем папку, если её нет
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # Получаем ID пользователя
    user_id = data.get('message', {}).get('from', {}).get('id')
    if not user_id:
        return None
        
    # Получаем токен бота из переменных окружения
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not bot_token:
        logging.error("Не найден токен бота в переменных окружения. Проверьте файл .env")
        # Выводим путь к файлу .env для отладки
        logging.info(f"Путь к файлу .env: {env_path}")
        return None
    
    # Запрашиваем фото профиля пользователя через API
    url = f"https://api.telegram.org/bot{bot_token}/getUserProfilePhotos"
    params = {
        "user_id": user_id,
        "limit": 1
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logging.error(f"Ошибка при запросе фото профиля: {response.text}")
            return None
            
        result = response.json()
        if not result.get('ok') or not result.get('result', {}).get('photos'):
            return None
            
        photos = result['result']['photos']
        if not photos or not photos[0]:
            return None
            
        # Берем первое фото, максимальное качество
        file_id = photos[0][-1]['file_id']
        
        # Получаем информацию о файле через Telegram API
        file_url = f"https://api.telegram.org/bot{bot_token}/getFile"
        file_params = {"file_id": file_id}
        file_response = requests.get(file_url, params=file_params)
        
        if file_response.status_code != 200:
            logging.error(f"Ошибка при получении информации о файле: {file_response.text}")
            return None
            
        file_path = file_response.json().get('result', {}).get('file_path')
        if not file_path:
            return None
            
        # Генерируем имя файла
        file_name = f"{user_id}_avatar.jpg"
        full_path = os.path.join(save_folder, file_name)
        
        # Скачиваем файл
        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        img_response = requests.get(download_url)
        
        if img_response.status_code != 200:
            logging.error(f"Ошибка при скачивании аватарки: {img_response.status_code}")
            return None
            
        # Сохраняем файл
        with open(full_path, 'wb') as f:
            f.write(img_response.content)
            
        return file_name
    except Exception as e:
        logging.error(f"Ошибка при получении аватарки пользователя: {e}")
        return None


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = context.user_data.get('lang', 'en')
    await query.answer()

    if query.data == 'request_location':
        await query.edit_message_text(
            text=get_text('location_request', lang),
            reply_markup=get_back_keyboard(lang)
        )
    
    elif query.data == 'help':
        await query.edit_message_text(
            text=get_text('help', lang),
            reply_markup=get_back_keyboard(lang)
        )
    
    elif query.data == 'back':
        await query.edit_message_text(
            text=get_text('start', lang, user=update.effective_user.first_name),
            reply_markup=get_main_keyboard(lang)
        )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    lang = context.user_data.get('lang', 'en')

    # Проверяем, содержит ли сообщение геопозицию
    if update.message.location:
        location = update.message.location
        
        # Сохраняем местоположение пользователя в базу
        conn = db.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO telegram_users_locations (user_id, lat, lon, last_update)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """, (
                str(user.id),
                location.latitude,
                location.longitude
            ))
            conn.commit()
            logging.info(f"Местоположение пользователя {user.id} сохранено в базе данных")
        except Exception as e:
            logging.error(f"Ошибка при сохранении местоположения: {e}")
            if conn.in_transaction:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            db.pool.release_connection(conn)

        # Обновляем сообщение с подтверждением
        await context.bot.edit_message_text(
            text=get_text('location_received', lang, lat=location.latitude, lon=location.longitude),
            chat_id=update.effective_chat.id,
            message_id=context.user_data['last_message_id'],
            reply_markup=get_location_received_keyboard(lang)
        )
    else:
        await update.message.reply_text(get_text('location_required', lang))

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error_msg = f"Произошла ошибка: {context.error}"
    print(error_msg)
    # Можно добавить логирование в файл
    logging.error(error_msg)

# Добавьте эти функции в конец файла handlers.py

def handle_request_location(data):
    try:
        # Получаем данные из callback_query
        callback_query = data.get('callback_query', {})
        user_id = callback_query.get('from', {}).get('id')
        message_id = callback_query.get('message', {}).get('message_id')
        chat_id = callback_query.get('message', {}).get('chat', {}).get('id')
        
        # Определяем язык пользователя
        user_info = callback_query.get('from', {})
        lang = user_info.get('language_code', 'en')
        
        # Получаем клавиатуру в формате JSON
        keyboard = get_back_keyboard(lang)
        keyboard_dict = keyboard.to_dict() if hasattr(keyboard, 'to_dict') else {
            'inline_keyboard': [[{'text': btn.text, 'callback_data': btn.callback_data} for btn in row] for row in keyboard.inline_keyboard]
        }
        
        # Возвращаем ответ для webhook
        return jsonify({
            "method": "editMessageText",
            "chat_id": chat_id,
            "message_id": message_id,
            "text": get_text('location_request', lang),
            "reply_markup": keyboard_dict
        }), 200
    except Exception as e:
        logging.error(f"Ошибка в handle_request_location: {e}")
        return jsonify({"error": str(e)}), 500

def handle_help(data):
    try:
        # Получаем данные из callback_query
        callback_query = data.get('callback_query', {})
        user_id = callback_query.get('from', {}).get('id')
        message_id = callback_query.get('message', {}).get('message_id')
        chat_id = callback_query.get('message', {}).get('chat', {}).get('id')
        
        # Определяем язык пользователя
        user_info = callback_query.get('from', {})
        lang = user_info.get('language_code', 'en')
        
        # Получаем клавиатуру в формате JSON
        keyboard = get_back_keyboard(lang)
        keyboard_dict = keyboard.to_dict() if hasattr(keyboard, 'to_dict') else {
            'inline_keyboard': [[{'text': btn.text, 'callback_data': btn.callback_data} for btn in row] for row in keyboard.inline_keyboard]
        }
        
        # Возвращаем ответ для webhook
        return jsonify({
            "method": "editMessageText",
            "chat_id": chat_id,
            "message_id": message_id,
            "text": get_text('help', lang),
            "reply_markup": keyboard_dict
        }), 200
    except Exception as e:
        logging.error(f"Ошибка в handle_help: {e}")
        return jsonify({"error": str(e)}), 500

def handle_back(data):
    try:
        # Получаем данные из callback_query
        callback_query = data.get('callback_query', {})
        user_id = callback_query.get('from', {}).get('id')
        message_id = callback_query.get('message', {}).get('message_id')
        chat_id = callback_query.get('message', {}).get('chat', {}).get('id')
        
        # Определяем язык пользователя и имя пользователя
        user_info = callback_query.get('from', {})
        lang = user_info.get('language_code', 'en')
        first_name = user_info.get('first_name', '')
        
        # Получаем клавиатуру и преобразуем ее в JSON-совместимый формат
        keyboard = get_main_keyboard(lang)
        keyboard_dict = keyboard.to_dict() if hasattr(keyboard, 'to_dict') else {
            'inline_keyboard': [[{'text': btn.text, 'callback_data': btn.callback_data} for btn in row] for row in keyboard.inline_keyboard]
        }
        
        # Возвращаем ответ для webhook
        return jsonify({
            "method": "editMessageText",
            "chat_id": chat_id,
            "message_id": message_id,
            "text": get_text('start', lang, user=first_name),
            "reply_markup": keyboard_dict
        }), 200
    except Exception as e:
        logging.error(f"Ошибка в handle_back: {e}")
        return jsonify({"error": str(e)}), 500

def handle_location_webhook(data):
    try:
        # Получаем данные о местоположении
        message = data.get('message', {})
        location = message.get('location', {})
        user_id = message.get('from', {}).get('id')
        chat_id = message.get('chat', {}).get('id')
        
        # Определяем язык пользователя
        user_info = message.get('from', {})
        lang = user_info.get('language_code', 'en')
        
        # Сохраняем местоположение пользователя в базу
        latitude = location.get('latitude')
        longitude = location.get('longitude')
        
        # Исправляем ошибку: используем правильную таблицу telegram_users_locations
        conn = db.pool.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO telegram_users_locations (user_id, lat, lon, last_update)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """, (
                str(user_id),
                latitude,
                longitude
            ))
            conn.commit()
            logging.info(f"Местоположение пользователя {user_id} сохранено в базе данных")
        except Exception as e:
            logging.error(f"Ошибка при сохранении местоположения: {e}")
            if conn.in_transaction:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            db.pool.release_connection(conn)
        
        # Получаем клавиатуру в формате JSON
        keyboard = get_location_received_keyboard(lang)
        keyboard_dict = keyboard.to_dict() if hasattr(keyboard, 'to_dict') else {
            'inline_keyboard': [[{'text': btn.text, 'callback_data': btn.callback_data} for btn in row] for row in keyboard.inline_keyboard]
        }
        
        # Возвращаем ответ для webhook
        return jsonify({
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": get_text('location_received', lang, lat=latitude, lon=longitude),
            "reply_markup": keyboard_dict
        }), 200
    except Exception as e:
        logging.error(f"Ошибка в handle_location_webhook: {e}")
        return jsonify({"error": str(e)}), 500