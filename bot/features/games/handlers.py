
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from bot.features.games.catalog import GAMES
from bot.common.keyboards import back_to_menu

router = Router()


def games_keyboard():
    buttons = []

    for game_id, game_name in GAMES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"🎮 {game_name}",
                callback_data=f"game:{game_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Главное меню",
            callback_data="menu:home"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


@router.callback_query(F.data == "menu:games")
async def games_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎮 ИГРЫ SUPERQUEST\n\n"
        "Выбери игру, чтобы посмотреть "
        "доступные задания и конкурсы.",
        reply_markup=games_keyboard()
    )

    await callback.answer()


@router.callback_query(F.data.startswith("game:"))
async def selected_game(callback: CallbackQuery):
    game_id = callback.data.split(":", 1)[1]
    game_name = GAMES.get(game_id)

    if not game_name:
        await callback.answer(
            "Игра не найдена",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        f"🎮 {game_name}\n\n"
        "🏆 Конкурсы этой игры скоро появятся.",
        reply_markup=back_to_menu()
    )

    await callback.answer()
