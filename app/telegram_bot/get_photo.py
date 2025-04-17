import os
import requests
from telegram import Update
from telegram.ext import ContextTypes

SAVE_FOLDER = 'photos'
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

async def save_user_avatar(update: Update, context: ContextTypes.DEFAULT_TYPE, save_folder: str = 'photos') -> str:
    """
    Получает и сохраняет аватарку пользователя с использованием requests.
    
    Аргументы:
        update: объект Update от telegram
        context: объект ContextTypes от telegram
        save_folder: папка для сохранения (по умолчанию 'photos')
    
    Возвращает:
        str: сообщение о результате (например, путь к файлу или ошибка)
    """
    # Создаем папку, если её нет
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # Получаем ID пользователя
    user_id = update.message.from_user.id

    # Запрашиваем фото профиля пользователя
    profile_photos = await context.bot.get_user_profile_photos(user_id, limit=1)

    if profile_photos.photos:
        # Берем первое фото, максимальное качество
        photo = profile_photos.photos[0][-1]
        file_id = photo.file_id

        # Получаем информацию о файле через Telegram API
        file = await context.bot.get_file(file_id)
        file_url = file.file_path  # URL файла

        # Генерируем имя файла без указания папки в возвращаемом значении
        file_name = f"{user_id}_avatar.jpg"
        file_path = os.path.join(save_folder, file_name)

        # Скачиваем файл с помощью requests
        response = requests.get(file_url)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return file_name  # Возвращаем только имя файла
        else:
            return 'Ошибка при скачивании аватарки!'
    else:
        return None