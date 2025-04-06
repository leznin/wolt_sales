# handlers.py
from telegram import Update
from telegram.ext import ContextTypes
from messages import get_text
from keyboards import get_main_keyboard, get_back_keyboard, get_location_received_keyboard
from database import WoltTelegramDatabase
from get_photo import save_user_avatar
import logging

db = WoltTelegramDatabase()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем объект пользователя целиком
    user = update.message.from_user
    lang = user.language_code or 'en'

    # получаем фото
    photo = await save_user_avatar(update, context)

    # Сохраняем данные пользователя в базу
    user_data = {
        'user_id': str(user.id),  # Уникальный идентификатор пользователя
        'name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'lang': user.language_code or 'en',
        'url_photo': photo,
        'premium': str(user.is_premium) if user.is_premium is not None else 'false'
    }
    db.update_telegram_user(user_data)

    # Отправляем приветственное сообщение
    message = await update.message.reply_text(
        get_text('start', lang, user=user.first_name),
        reply_markup=get_main_keyboard(lang)
    )
    context.user_data['last_message_id'] = message.message_id
    context.user_data['lang'] = lang

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
            reply_markup=get_main_keyboard(lang)
        )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    # Проверяем, содержит ли сообщение геопозицию
    if update.message.location:
        location = update.message.location
        lang = context.user_data.get('lang', 'en')
        # Сохраняем местоположение пользователя в базу
        db.update_user_location(str(user.id), location.latitude, location.longitude)

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