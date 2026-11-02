
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.common.keyboards import back_to_menu

router = Router()


@router.callback_query(F.data == "menu:submissions")
async def submissions_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "📹 МОИ ЗАЯВКИ\n\n"
        "Здесь ты сможешь отслеживать "
        "отправленные игровые видео.\n\n"
        "⏳ На проверке\n"
        "✅ Принято\n"
        "❌ Отклонено\n"
        "🏆 Победитель\n\n"
        "Система заявок находится в разработке.",
        reply_markup=back_to_menu()
    )

    await callback.answer()
