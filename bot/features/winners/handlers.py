
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.common.keyboards import back_to_menu

router = Router()


@router.callback_query(F.data == "menu:winners")
async def winners_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "🥇 ПОБЕДИТЕЛИ SUPERQUEST\n\n"
        "🏆 Здесь будут публиковаться "
        "победители игровых конкурсов.\n\n"
        "Также появятся:\n"
        "🥇 Рейтинг игроков\n"
        "🎮 Лучшие игровые моменты\n"
        "💰 Выигранные призы",
        reply_markup=back_to_menu()
    )

    await callback.answer()
