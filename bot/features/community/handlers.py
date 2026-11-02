
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.common.keyboards import back_to_menu

router = Router()


@router.callback_query(F.data == "menu:community")
async def community_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "👥 СООБЩЕСТВО SUPERQUEST\n\n"
        "Здесь появятся ссылки на:\n\n"
        "📢 Канал с объявлениями\n"
        "💬 Группу игроков\n"
        "🏆 Обсуждение конкурсов\n\n"
        "Ссылки будут добавлены после "
        "создания сообществ.",
        reply_markup=back_to_menu()
    )

    await callback.answer()
