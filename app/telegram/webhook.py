# telegram/webhook.py
import hmac
import hashlib
import urllib.parse
import json

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

def process_webhook(data):
    init_data = data.get('initData', '')
    if not init_data:
        return {"error": "No initData provided"}, 400

    # Парсинг initData
    parsed_data = dict(urllib.parse.parse_qsl(init_data))
    received_hash = parsed_data.pop('hash', '')

    # Создание строки для проверки подписи
    data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    secret_key = hmac.new("WebAppData".encode(), BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != received_hash:
        return {"error": "Invalid initData signature"}, 403

    # Извлечение данных о пользователе
    user_data = json.loads(parsed_data.get('user', '{}'))
    return {
        "status": "success",
        "user": user_data
    }, 200