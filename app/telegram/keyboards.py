
# keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from messages import get_text

def get_main_keyboard(lang='ru'):
    keyboard = [
        [InlineKeyboardButton(get_text('btn_send_location', lang), callback_data='request_location')],
        [InlineKeyboardButton(get_text('btn_help', lang), callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard(lang='ru'):
    keyboard = [
        [InlineKeyboardButton(get_text('btn_back', lang), callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_location_received_keyboard(lang='ru'):
    keyboard = [
        [InlineKeyboardButton(get_text('btn_send_again', lang), callback_data='request_location')],
        [InlineKeyboardButton(get_text('btn_back', lang), callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)