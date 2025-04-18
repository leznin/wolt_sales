from flask import jsonify, request
import urllib
import hmac
import hashlib
import json
from dotenv import load_dotenv
import os
import logging
import sys
import threading
import requests
from .handlers import (
    start_command, 
    handle_request_location, 
    handle_help, 
    handle_back, 
    handle_location_webhook
)

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(root_dir)
from database import WoltDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env')
load_dotenv(dotenv_path=env_path)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
logger.info(f"Bot token: {TELEGRAM_TOKEN}")

db = WoltDatabase()
db_local = threading.local()  # Определяем db_local здесь

def get_db():
    if not hasattr(db_local, 'db'):
        try:
            db_local.db = WoltDatabase()
            logger.info(f"111 Database initialized for thread {threading.get_ident()}")
        except Exception as e:
            logger.error(f"2222 Error initializing database for thread {threading.get_ident()}: {e}")
            db_local.db = None
    return db_local.db


def webhook():
    data = request.json
    logger.info(f"Received data: {data}")
    init_data_str = data.get('initData', '')
    
    message = data.get('message', {})
    callback_query = data.get('callback_query', {})
    command = message.get('text', '')

    user_id = None
    message_saved = False  # Track if a message was saved

    if message:
        user_id = str(message.get('from', {}).get('id', ''))
        # Save text message only if it does NOT start with "/"
        if 'text' in message and not message['text'].startswith('/'):
            get_db().save_user_message(user_id, 'text', message['text'])
            message_saved = True
        elif 'photo' in message:
            # Download the largest photo
            photo = message['photo'][-1] if message['photo'] else None
            caption = message.get('caption', None)
            if photo:
                local_path = download_telegram_file(photo.get('file_id'))
                get_db().save_user_message(
                    user_id, 'photo', caption,  # Save caption as content
                    file_id=photo.get('file_id'),
                    file_unique_id=photo.get('file_unique_id'),
                    file_name=local_path  # Save local file path as file_name
                )
                message_saved = True
        elif 'audio' in message:
            audio = message['audio']
            caption = message.get('caption', None)
            local_path = download_telegram_file(audio.get('file_id'))
            get_db().save_user_message(
                user_id, 'audio', caption,
                file_id=audio.get('file_id'),
                file_unique_id=audio.get('file_unique_id'),
                file_name=local_path
            )
            message_saved = True
        elif 'video' in message:
            video = message['video']
            caption = message.get('caption', None)
            local_path = download_telegram_file(video.get('file_id'))
            get_db().save_user_message(
                user_id, 'video', caption,
                file_id=video.get('file_id'),
                file_unique_id=video.get('file_unique_id'),
                file_name=local_path
            )
            message_saved = True
        elif 'document' in message:
            doc = message['document']
            caption = message.get('caption', None)
            local_path = download_telegram_file(doc.get('file_id'))
            get_db().save_user_message(
                user_id, 'document', caption,
                file_id=doc.get('file_id'),
                file_unique_id=doc.get('file_unique_id'),
                file_name=local_path
            )
            message_saved = True
        elif 'voice' in message:
            voice = message['voice']
            caption = message.get('caption', None)  # Обычно у voice нет caption, но пусть будет для совместимости
            local_path = download_telegram_file(voice.get('file_id'))
            get_db().save_user_message(
                user_id, 'voice', caption,
                file_id=voice.get('file_id'),
                file_unique_id=voice.get('file_unique_id'),
                file_name=local_path
            )
            message_saved = True
        elif 'sticker' in message:
            sticker = message['sticker']
            caption = message.get('caption', None)
            local_path = download_telegram_file(sticker.get('file_id'))
            get_db().save_user_message(
                user_id, 'sticker', caption,
                file_id=sticker.get('file_id'),
                file_unique_id=sticker.get('file_unique_id'),
                file_name=local_path
            )
            message_saved = True
        elif 'video_note' in message:
            video_note = message['video_note']
            caption = message.get('caption', None)
            local_path = download_telegram_file(video_note.get('file_id'))
            get_db().save_user_message(
                user_id, 'video_note', caption,
                file_id=video_note.get('file_id'),
                file_unique_id=video_note.get('file_unique_id'),
                file_name=local_path
            )
            message_saved = True

    # If any message was saved, return success
    if message_saved:
        return jsonify({"status": "message saved"}), 200

    # Обработка initData (для веб-приложений)
    if init_data_str:
        return process_init_data(data)
    
    # Обработка callback_query (для кнопок)
    elif callback_query:
        query_data = callback_query.get('data', '')
        
        if query_data == 'request_location':
            return handle_request_location(data)
        elif query_data == 'help':
            return handle_help(data)
        elif query_data == 'back':
            return handle_back(data)
        else:
            return jsonify({"error": "Unknown callback query"}), 400
    
    # Обработка команд
    elif command:
        if command == '/start':
            return start_command(data)
        else:
            return jsonify({"status": "message saved"}), 200
    
    # Обработка местоположения
    elif message.get('location'):
        return handle_location_webhook(data)
    
    return jsonify({"error": "No valid data provided"}), 402


def process_init_data(data):
    data = request.json
    init_data = data.get('initData', '')
    fingerprint = data.get('fingerprint', '')
    if not init_data:
        return jsonify({"error": "No initData provided"}), 400    
    parsed_data = dict(urllib.parse.parse_qsl(init_data))
    received_hash = parsed_data.pop('hash', '')

    data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    secret_key = hmac.new("WebAppData".encode(), TELEGRAM_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != received_hash:
        return jsonify({"error": "Invalid initData signature"}), 403
    
    user_data = json.loads(parsed_data.get('user', '{}'))
    
    ip_address = request.remote_addr
    if 'X-Forwarded-For' in request.headers:
        ip_address = request.headers['X-Forwarded-For'].split(',')[0].strip()

    if user_data and fingerprint:
        save_user_data(user_data, fingerprint, ip_address)

    avatar_path = get_user_avatar(user_data['id'])
    user_data['url_photo'] = avatar_path
    logging.info(f"111 - User {user_data['id']} avatar path: {avatar_path}")

    return jsonify({
        "status": "success",
        "user": user_data,
        "avatarPath": avatar_path
    }), 200
    

def save_user_data(user_data, fingerprint, ip_address):
    db_instance = get_db()
    conn = db_instance.pool.get_connection()
    cursor = None
    result = False
    try:
        cursor = conn.cursor()
        
        # Сначала проверяем, существует ли пользователь
        cursor.execute("""
            SELECT user_id FROM telegram_users WHERE user_id = %s
        """, (str(user_data.get('id')),))
        
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
                    pm_enabled = %s,
                    fingerprintjs = %s,
                    ip_open_app = %s,
                    last_update = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (
                user_data.get('first_name', ''),
                user_data.get('last_name', ''),
                user_data.get('username', ''),
                user_data.get('language_code', 'en'),
                str(user_data.get('is_premium', False)).lower(),
                str(user_data.get('allows_write_to_pm', True)).lower(),
                fingerprint,
                ip_address,
                str(user_data.get('id'))
            ))
        else:
            # Если пользователь не существует, вставляем новую запись
            cursor.execute("""
                INSERT INTO telegram_users (
                    user_id, name, last_name, username, lang, premium, pm_enabled, ip_open_app
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(user_data.get('id')),
                user_data.get('first_name', ''),
                user_data.get('last_name', ''),
                user_data.get('username', ''),
                user_data.get('language_code', 'en'),
                str(user_data.get('is_premium', False)).lower(),
                str(user_data.get('allows_write_to_pm', True)).lower(),
                fingerprint,
                ip_address
            ))
        
        conn.commit()
        logger.info(f"User {user_data.get('id')} saved with fingerprint {fingerprint} and IP {ip_address}")
        result = True
    except Exception as e:
        logger.error(f"Error saving user data: {e}")
        conn.rollback()
    finally:
        if cursor:
            cursor.close()
        db_instance.pool.release_connection(conn)
    return result

def get_user_avatar(user_id):
    conn = db.pool.get_connection()
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT url_photo FROM telegram_users WHERE user_id = %s
        """, (str(user_id),))
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]  # Вернет photos/415409454_avatar.jpg
        return None
    except Exception as e:
        logger.error(f"Error retrieving avatar for user {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        db.pool.release_connection(conn)



def download_telegram_file(file_id, save_dir='user_uploads'):
    """
    Downloads a file from Telegram and saves it locally.
    Returns the local file path.
    """
    # Ensure save_dir exists
    os.makedirs(save_dir, exist_ok=True)
    # Get file path from Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
    resp = requests.get(url)
    if resp.status_code != 200:
        logger.error(f"Failed to get file info from Telegram: {resp.text}")
        return None
    file_path = resp.json()['result']['file_path']
    # Download the file
    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
    local_filename = os.path.join(save_dir, os.path.basename(file_path))
    file_resp = requests.get(file_url)
    if file_resp.status_code == 200:
        with open(local_filename, 'wb') as f:
            f.write(file_resp.content)
        return local_filename
    else:
        logger.error(f"Failed to download file from Telegram: {file_resp.text}")
        return None

