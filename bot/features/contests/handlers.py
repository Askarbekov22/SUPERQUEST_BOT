
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.common.keyboards import back_to_menu

router = Router()


@router.callback_query(F.data == "menu:contests")
async def contests_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏆 КОНКУРСЫ SUPERQUEST\n\n"
        "Здесь будут отображаться:\n\n"
        "🟢 Активные конкурсы\n"
        "⏳ Скоро начнутся\n"
        "✅ Завершённые конкурсы\n\n"
        "В каждом конкурсе будут указаны "
        "задание, призовой фонд и сроки.",
        reply_markup=back_to_menu()
    )

    await callback.answer()
