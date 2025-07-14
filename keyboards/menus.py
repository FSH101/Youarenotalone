# keyboards/menus.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Поговорить")],
            [KeyboardButton(text="🎧 Слушать мысли")],
            [KeyboardButton(text="🗂 Мои мысли")],
            [KeyboardButton(text="💬 Что мне сказали")]
        ],
        resize_keyboard=True
    )