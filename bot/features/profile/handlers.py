
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.common.keyboards import back_to_menu

router = Router()


@router.callback_query(F.data == "menu:profile")
async def profile_handler(callback: CallbackQuery):
    user = callback.from_user

    username = (
        f"@{user.username}"
        if user.username
        else "Не указан"
    )

    await callback.message.edit_text(
        "👤 МОЙ ПРОФИЛЬ\n\n"
        f"Имя: {user.full_name}\n"
        f"Username: {username}\n"
        f"Telegram ID: {user.id}\n\n"
        "🏆 Победы: скоро\n"
        "🎮 Любимые игры: скоро\n"
        "💰 Выиграно: скоро",
        reply_markup=back_to_menu()
    )

    await callback.answer()
