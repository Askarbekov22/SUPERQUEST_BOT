
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.common.keyboards import back_to_menu

from bot.database.storage import get_user_games
from bot.features.games.catalog import GAMES


router = Router()


@router.callback_query(F.data == "menu:profile")
async def profile_handler(callback: CallbackQuery):

    user = callback.from_user

    user_id = user.id

    username = (
        f"@{user.username}"
        if user.username
        else "Не указан"
    )

    selected_games = await get_user_games(
        user_id
    )

    if selected_games:

        games_list = "\n".join(
            f"• {game_name}"
            for game_id, game_name in GAMES.items()
            if game_id in selected_games
        )

    else:
        games_list = "Пока не выбраны"

    profile_text = (
        "👤 МОЙ ПРОФИЛЬ\n\n"
        f"Имя: {user.full_name}\n"
        f"Username: {username}\n"
        f"Telegram ID: {user_id}\n\n"
        "🎮 МОИ ИГРЫ:\n"
        f"{games_list}\n\n"
        "📊 СТАТИСТИКА:\n"
        "🏆 Победы: скоро\n"
        "📹 Отправлено видео: скоро\n"
        "💰 Выиграно: скоро"
    )

    await callback.message.edit_text(
        profile_text,
        reply_markup=back_to_menu()
    )

    await callback.answer()
