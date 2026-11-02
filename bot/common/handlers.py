
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from bot.common.keyboards import main_menu

router = Router()

WELCOME_TEXT = (
    "🎮 SUPERQUEST\n\n"
    "Добро пожаловать в мир игровых челленджей!\n\n"
    "🏆 Выполняй задания\n"
    "🎮 Соревнуйся с игроками\n"
    "💰 Выигрывай денежные призы\n\n"
    "Выбери нужный раздел:"
)


@router.message(CommandStart())
@router.message(Command("menu"))
async def start_handler(message: Message):
    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_menu()
    )


@router.callback_query(F.data == "menu:home")
async def home_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        WELCOME_TEXT,
        reply_markup=main_menu()
    )

    await callback.answer()
