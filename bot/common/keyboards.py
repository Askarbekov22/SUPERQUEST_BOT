
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)


def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏆 Конкурсы",
                    callback_data="menu:contests"
                ),
                InlineKeyboardButton(
                    text="🎮 Игры",
                    callback_data="menu:games"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📹 Мои заявки",
                    callback_data="menu:submissions"
                ),
                InlineKeyboardButton(
                    text="🥇 Победители",
                    callback_data="menu:winners"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 Профиль",
                    callback_data="menu:profile"
                ),
                InlineKeyboardButton(
                    text="👥 Сообщество",
                    callback_data="menu:community"
                )
            ]
        ]
    )


def back_to_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Главное меню",
                    callback_data="menu:home"
                )
            ]
        ]
    )
