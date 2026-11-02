
from aiogram import Router, F

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from bot.features.games.catalog import GAMES

from bot.database.storage import (
    get_user_games,
    toggle_user_game
)


router = Router()


def games_keyboard(selected_games: set[str]):
    """Кнопки выбора любимых игр."""

    buttons = []

    for game_id, game_name in GAMES.items():

        is_selected = game_id in selected_games

        icon = "✅" if is_selected else "⬜"

        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} {game_name}",
                callback_data=f"games:toggle:{game_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="menu:home"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def games_text(selected_games: set[str]):
    """Текст экрана выбора игр."""

    count = len(selected_games)

    return (
        "🎮 МОИ ИГРЫ\n\n"
        "Выбери игры, которые тебе интересны.\n\n"
        "Ты сможешь участвовать в конкурсах "
        "по выбранным играм и получать "
        "уведомления о новых заданиях.\n\n"
        f"✅ Выбрано игр: {count}\n\n"
        "Нажми на игру, чтобы добавить "
        "или убрать её из списка.\n\n"
        "💾 Изменения сохраняются автоматически."
    )


@router.callback_query(F.data == "menu:games")
async def games_handler(callback: CallbackQuery):

    user_id = callback.from_user.id

    selected_games = await get_user_games(
        user_id
    )

    await callback.message.edit_text(
        games_text(selected_games),
        reply_markup=games_keyboard(
            selected_games
        )
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("games:toggle:")
)
async def toggle_game_handler(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    game_id = callback.data.split(":", 2)[2]

    game_name = GAMES.get(game_id)

    if not game_name:
        await callback.answer(
            "Игра не найдена",
            show_alert=True
        )
        return

    is_selected = await toggle_user_game(
        user_id,
        game_id
    )

    selected_games = await get_user_games(
        user_id
    )

    await callback.message.edit_text(
        games_text(selected_games),
        reply_markup=games_keyboard(
            selected_games
        )
    )

    if is_selected:
        await callback.answer(
            f"✅ {game_name} добавлена"
        )
    else:
        await callback.answer(
            f"❌ {game_name} удалена"
        )

