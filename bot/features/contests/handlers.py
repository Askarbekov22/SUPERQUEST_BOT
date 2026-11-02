
import time
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message
)

from config import ADMIN_IDS
from bot.features.games.catalog import GAMES
from bot.features.contests.states import NewContest
from bot.features.contests.repository import (
    create_contest,
    get_contest,
    list_contests
)


router = Router()
KG_TIME = timezone(timedelta(hours=6))


# ======================================
# КЛАВИАТУРЫ
# ======================================

def keyboard(rows):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=data
                )
                for text, data in row
            ]
            for row in rows
        ]
    )


def admin_keyboard():
    return keyboard([
        [("➕ Создать конкурс", "admin:create")],
        [("📋 Все конкурсы", "contests:list:all")],
        [("🏠 Главное меню", "menu:home")]
    ])


def contests_keyboard():
    return keyboard([
        [("🟢 Активные", "contests:list:active")],
        [("⏳ Скоро начнутся", "contests:list:upcoming")],
        [("✅ Завершённые", "contests:list:finished")],
        [("🏠 Главное меню", "menu:home")]
    ])


def cancel_keyboard():
    return keyboard([
        [("❌ Отменить создание", "admin:cancel")]
    ])


def game_keyboard():
    rows = [
        [(name, f"admin:game:{game_id}")]
        for game_id, name in GAMES.items()
    ]

    rows.append([
        ("❌ Отмена", "admin:cancel")
    ])

    return keyboard(rows)


# ======================================
# ВРЕМЯ И ФОРМАТИРОВАНИЕ
# ======================================

def format_date(timestamp):
    return datetime.fromtimestamp(
        timestamp,
        KG_TIME
    ).strftime("%d.%m.%Y %H:%M")


def parse_date(value):
    try:
        date = datetime.strptime(
            value,
            "%d.%m.%Y %H:%M"
        )

        return int(
            date.replace(tzinfo=KG_TIME).timestamp()
        )

    except ValueError:
        return None


def get_status(contest):
    now = int(time.time())

    if now < contest["starts_at"]:
        return "⏳ Скоро начнётся"

    if now >= contest["ends_at"]:
        return "✅ Завершён"

    return "🟢 Активен"


def format_contest(contest):
    game_name = GAMES.get(
        contest["game_id"],
        "Неизвестная игра"
    )

    return (
        f"🏆 КОНКУРС №{contest['id']}\n\n"
        f"🎮 Игра: {game_name}\n"
        f"📌 Название: {contest['title']}\n"
        f"📊 Статус: {get_status(contest)}\n\n"
        f"💰 Призовой фонд: "
        f"{contest['prize_som']:,} сом\n\n"
        f"🟢 Начало: "
        f"{format_date(contest['starts_at'])}\n"
        f"🔴 Окончание: "
        f"{format_date(contest['ends_at'])}\n"
        f"🕒 Время Бишкека\n\n"
        f"🎯 ЗАДАНИЕ:\n{contest['task']}\n\n"
        f"⚖️ КРИТЕРИИ ПОБЕДЫ:\n"
        f"{contest['criteria']}\n\n"
        "📹 Отправка видео доступна через "
        "раздел «Мои заявки», если установлен "
        "модуль приёма видео."
    )


# ======================================
# TELEGRAM ID
# ======================================

@router.message(Command("myid"))
async def my_id_handler(message: Message):
    await message.answer(
        f"🆔 Твой Telegram ID:\n"
        f"{message.from_user.id}"
    )


# ======================================
# АДМИН-ПАНЕЛЬ
# ======================================

@router.message(Command("admin"))
async def admin_handler(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        await message.answer(
            "⛔ У тебя нет доступа к админ-панели.\n\n"
            "Проверь ADMIN_IDS в файле .env."
        )
        return

    await message.answer(
        "⚙️ АДМИН-ПАНЕЛЬ SUPERQUEST\n\n"
        "Выбери действие:",
        reply_markup=admin_keyboard()
    )


@router.callback_query(F.data == "admin:menu")
async def admin_menu_handler(callback: CallbackQuery):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "⚙️ АДМИН-ПАНЕЛЬ SUPERQUEST\n\n"
        "Выбери действие:",
        reply_markup=admin_keyboard()
    )

    await callback.answer()


# ======================================
# СОЗДАНИЕ КОНКУРСА
# ======================================

@router.callback_query(F.data == "admin:create")
async def create_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    await state.clear()
    await state.set_state(NewContest.game)

    await callback.message.edit_text(
        "🎮 СОЗДАНИЕ КОНКУРСА\n\n"
        "Шаг 1/7\n"
        "Выбери игру:",
        reply_markup=game_keyboard()
    )

    await callback.answer()


@router.callback_query(F.data == "admin:cancel")
async def cancel_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()

    await callback.message.edit_text(
        "❌ Создание конкурса отменено.",
        reply_markup=admin_keyboard()
    )

    await callback.answer()


# ======================================
# ШАГ 1. ИГРА
# ======================================

@router.callback_query(
    NewContest.game,
    F.data.startswith("admin:game:")
)
async def set_game(
    callback: CallbackQuery,
    state: FSMContext
):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return

    game_id = callback.data.split(":", 2)[2]

    if game_id not in GAMES:
        await callback.answer(
            "Игра не найдена",
            show_alert=True
        )
        return

    await state.update_data(game_id=game_id)
    await state.set_state(NewContest.title)

    await callback.message.edit_text(
        "📝 Шаг 2/7\n\n"
        "Напиши название конкурса.\n\n"
        "Например: Победа 1 против 3",
        reply_markup=cancel_keyboard()
    )

    await callback.answer()


# ======================================
# ШАГ 2. НАЗВАНИЕ
# ======================================

@router.message(NewContest.title)
async def set_title(
    message: Message,
    state: FSMContext
):

    if message.from_user.id not in ADMIN_IDS:
        return

    title = (message.text or "").strip()

    if not 4 <= len(title) <= 100:
        await message.answer(
            "Название должно содержать "
            "от 4 до 100 символов."
        )
        return

    await state.update_data(title=title)
    await state.set_state(NewContest.task)

    await message.answer(
        "🎯 Шаг 3/7\n\n"
        "Опиши задание для игроков.\n\n"
        "Например: Победи трёх противников "
        "в одиночку и запиши момент победы.",
        reply_markup=cancel_keyboard()
    )


# ======================================
# ШАГ 3. ЗАДАНИЕ
# ======================================

@router.message(NewContest.task)
async def set_task(
    message: Message,
    state: FSMContext
):

    if message.from_user.id not in ADMIN_IDS:
        return

    task = (message.text or "").strip()

    if not 10 <= len(task) <= 800:
        await message.answer(
            "Задание должно содержать "
            "от 10 до 800 символов."
        )
        return

    await state.update_data(task=task)
    await state.set_state(NewContest.criteria)

    await message.answer(
        "⚖️ Шаг 4/7\n\n"
        "Напиши критерии выбора победителя.\n\n"
        "Например: Победит участник "
        "с самым быстрым выполнением задания.",
        reply_markup=cancel_keyboard()
    )


# ======================================
# ШАГ 4. КРИТЕРИИ ПОБЕДЫ
# ======================================

@router.message(NewContest.criteria)
async def set_criteria(
    message: Message,
    state: FSMContext
):

    if message.from_user.id not in ADMIN_IDS:
        return

    criteria = (message.text or "").strip()

    if not 10 <= len(criteria) <= 400:
        await message.answer(
            "Критерии должны содержать "
            "от 10 до 400 символов."
        )
        return

    await state.update_data(criteria=criteria)
    await state.set_state(NewContest.prize)

    await message.answer(
        "💰 Шаг 5/7\n\n"
        "Введи общий призовой фонд в сомах.\n\n"
        "Например: 3000",
        reply_markup=cancel_keyboard()
    )


# ======================================
# ШАГ 5. ПРИЗОВОЙ ФОНД
# ======================================

@router.message(NewContest.prize)
async def set_prize(
    message: Message,
    state: FSMContext
):

    if message.from_user.id not in ADMIN_IDS:
        return

    value = (message.text or "").strip()

    if (
        not value.isascii()
        or not value.isdecimal()
        or not 1 <= int(value) <= 1_000_000
    ):
        await message.answer(
            "Введи сумму цифрами "
            "от 1 до 1 000 000 сом."
        )
        return

    await state.update_data(prize_som=int(value))
    await state.set_state(NewContest.start)

    await message.answer(
        "🟢 Шаг 6/7\n\n"
        "Введи дату и время начала.\n"
        "Формат: 05.11.2026 18:00\n\n"
        "Или напиши: сейчас",
        reply_markup=cancel_keyboard()
    )


# ======================================
# ШАГ 6. НАЧАЛО
# ======================================

@router.message(NewContest.start)
async def set_start(
    message: Message,
    state: FSMContext
):

    if message.from_user.id not in ADMIN_IDS:
        return

    value = (message.text or "").strip()

    if value.lower() == "сейчас":
        start_time = int(time.time())
    else:
        start_time = parse_date(value)

    if start_time is None:
        await message.answer(
            "Неверный формат даты.\n"
            "Пример: 05.11.2026 18:00"
        )
        return

    if start_time < int(time.time()) - 120:
        await message.answer(
            "Дата начала не может быть в прошлом."
        )
        return

    await state.update_data(starts_at=start_time)
    await state.set_state(NewContest.end)

    await message.answer(
        "🔴 Шаг 7/7\n\n"
        "Введи дату и время окончания.\n"
        "Например: 10.11.2026 20:00",
        reply_markup=cancel_keyboard()
    )


# ======================================
# ШАГ 7. ОКОНЧАНИЕ
# ======================================

@router.message(NewContest.end)
async def set_end(
    message: Message,
    state: FSMContext
):

    if message.from_user.id not in ADMIN_IDS:
        return

    value = (message.text or "").strip()
    end_time = parse_date(value)

    data = await state.get_data()

    if end_time is None:
        await message.answer(
            "Неверный формат даты.\n"
            "Пример: 10.11.2026 20:00"
        )
        return

    if (
        end_time <= data["starts_at"]
        or end_time <= int(time.time())
    ):
        await message.answer(
            "Окончание должно быть позже начала "
            "и находиться в будущем."
        )
        return

    await state.update_data(ends_at=end_time)
    await state.set_state(NewContest.confirm)

    data = await state.get_data()

    preview = {
        "id": "НОВЫЙ",
        **data
    }

    await message.answer(
        "📋 ПРОВЕРЬ КОНКУРС\n\n"
        + format_contest(preview),
        reply_markup=keyboard([
            [("✅ Опубликовать", "admin:publish")],
            [("❌ Отмена", "admin:cancel")]
        ])
    )


# ======================================
# ПУБЛИКАЦИЯ
# ======================================

@router.callback_query(
    NewContest.confirm,
    F.data == "admin:publish"
)
async def publish_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return

    data = await state.get_data()

    required = {
        "game_id",
        "title",
        "task",
        "criteria",
        "prize_som",
        "starts_at",
        "ends_at"
    }

    if not required.issubset(data):
        await state.clear()
        await callback.answer(
            "Данные утеряны. Начни заново.",
            show_alert=True
        )
        return

    if data["ends_at"] <= int(time.time()):
        await callback.answer(
            "Время конкурса истекло. Создай новый.",
            show_alert=True
        )
        return

    contest_id = await create_contest(
        data,
        callback.from_user.id
    )

    await state.clear()

    await callback.message.edit_text(
        f"✅ КОНКУРС №{contest_id} СОЗДАН!\n\n"
        "Конкурс успешно сохранён и доступен "
        "игрокам в соответствующей категории.",
        reply_markup=admin_keyboard()
    )

    await callback.answer()


# ======================================
# МЕНЮ КОНКУРСОВ ДЛЯ ИГРОКОВ
# ======================================

@router.callback_query(F.data == "menu:contests")
async def contests_menu_handler(callback: CallbackQuery):

    await callback.message.edit_text(
        "🏆 КОНКУРСЫ SUPERQUEST\n\n"
        "Выбери категорию:",
        reply_markup=contests_keyboard()
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("contests:list:")
)
async def contests_list_handler(callback: CallbackQuery):

    category = callback.data.split(":", 2)[2]

    if category not in {
        "active", "upcoming", "finished", "all"
    }:
        await callback.answer(
            "Неизвестная категория",
            show_alert=True
        )
        return

    if (
        category == "all"
        and callback.from_user.id not in ADMIN_IDS
    ):
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    contests = await list_contests(category)

    titles = {
        "active": "🟢 АКТИВНЫЕ КОНКУРСЫ",
        "upcoming": "⏳ СКОРО НАЧНУТСЯ",
        "finished": "✅ ЗАВЕРШЁННЫЕ КОНКУРСЫ",
        "all": "📋 ВСЕ КОНКУРСЫ"
    }

    rows = []

    for contest in contests:
        game = GAMES.get(
            contest["game_id"],
            "Игра"
        )

        rows.append([
            (
                f"#{contest['id']} · {game} · "
                f"{contest['title'][:25]}",
                f"contests:open:{contest['id']}"
            )
        ])

    rows.append([
        ("⬅️ Назад", "menu:contests")
    ])

    description = (
        "Выбери конкурс:"
        if contests else
        "Конкурсов в этой категории пока нет."
    )

    await callback.message.edit_text(
        f"{titles[category]}\n\n{description}",
        reply_markup=keyboard(rows)
    )

    await callback.answer()


# ======================================
# ПРОСМОТР КОНКУРСА
# ======================================

@router.callback_query(
    F.data.startswith("contests:open:")
)
async def open_contest_handler(callback: CallbackQuery):

    contest_id = int(
        callback.data.rsplit(":", 1)[1]
    )

    contest = await get_contest(contest_id)

    if not contest:
        await callback.answer(
            "Конкурс не найден",
            show_alert=True
        )
        return

    rows = []

    if get_status(contest) == "🟢 Активен":
        rows.append([
            (
                "📤 Отправить видео",
                f"submissions:choose:{contest_id}"
            )
        ])

    rows.append([
        ("⬅️ К конкурсам", "menu:contests")
    ])

    await callback.message.edit_text(
        format_contest(contest),
        reply_markup=keyboard(rows)
    )

    await callback.answer()
