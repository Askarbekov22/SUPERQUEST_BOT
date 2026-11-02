
from datetime import datetime, timedelta, timezone
import time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message
)

from aiogram.exceptions import TelegramAPIError

from config import ADMIN_IDS
from bot.common.keyboards import back_to_menu

from bot.database.storage import (
    add_submission,
    get_contest,
    get_pending_submissions,
    get_submission,
    get_user_submissions,
    list_contests,
    review_submission
)

from bot.features.games.catalog import GAMES
from bot.features.submissions.states import VideoSubmission


router = Router()

KG_TZ = timezone(timedelta(hours=6))

STATUS_LABELS = {
    "pending": "⏳ На проверке",
    "approved": "✅ Принята",
    "rejected": "❌ Отклонена"
}


def kb(rows: list[list[tuple[str, str]]]):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=key
                )
                for text, key in row
            ]
            for row in rows
        ]
    )


def is_open(contest: dict) -> bool:
    now = int(time.time())
    return contest["starts_at"] <= now < contest["ends_at"]


def short_date(timestamp: int) -> str:
    return datetime.fromtimestamp(
        timestamp,
        KG_TZ
    ).strftime("%d.%m.%Y %H:%M")


# ====================================
# ЗАЯВКИ ИГРОКА
# ====================================

@router.callback_query(F.data == "menu:submissions")
async def my_submissions(callback: CallbackQuery):

    submissions = await get_user_submissions(
        callback.from_user.id
    )

    rows = [
        [("📤 Отправить видео", "submissions:pick")]
    ]

    for item in submissions:
        status = STATUS_LABELS.get(
            item["status"],
            item["status"]
        )

        rows.append([
            (
                f"#{item['id']} · {status}",
                f"submissions:mine:{item['id']}"
            )
        ])

    rows.append([
        ("🏠 Главное меню", "menu:home")
    ])

    caption = (
        "📹 МОИ ЗАЯВКИ\n\n"
        "Здесь отображаются отправленные "
        "записи и результаты проверки.\n"
        "Каждый игрок может отправить "
        "до 3 записей на конкурс.\n\n"
    )

    if submissions:
        caption += "Выбери заявку для просмотра:"
    else:
        caption += "Заявок пока нет."

    await callback.message.edit_text(
        caption,
        reply_markup=kb(rows)
    )

    await callback.answer()


# ====================================
# ВЫБОР КОНКУРСА
# ====================================

@router.message(Command("submit"))
async def submit_command(message: Message):

    contests = await list_contests(
        "active",
        limit=20
    )

    rows = [
        [
            (
                f"🎮 {GAMES.get(c['game_id'], 'Игра')} "
                f"· #{c['id']}",
                f"submissions:choose:{c['id']}"
            )
        ]
        for c in contests
    ]

    rows.append([
        ("🏠 Главное меню", "menu:home")
    ])

    text = (
        "📤 ОТПРАВИТЬ ВИДЕО\n\n"
        "Выбери активный конкурс:"
        if contests else
        "📤 ОТПРАВИТЬ ВИДЕО\n\n"
        "Сейчас нет активных конкурсов."
    )

    await message.answer(
        text,
        reply_markup=kb(rows)
    )


@router.callback_query(F.data == "submissions:pick")
async def choose_contest(callback: CallbackQuery):

    contests = await list_contests(
        "active",
        limit=20
    )

    rows = [
        [
            (
                f"🎮 {GAMES.get(c['game_id'], 'Игра')} "
                f"· #{c['id']}",
                f"submissions:choose:{c['id']}"
            )
        ]
        for c in contests
    ]

    rows.append([
        ("⬅️ К заявкам", "menu:submissions")
    ])

    text = (
        "📤 ВЫБОР КОНКУРСА\n\n"
        "Нажми на нужный конкурс:"
        if contests else
        "📤 ВЫБОР КОНКУРСА\n\n"
        "Активных конкурсов пока нет."
    )

    await callback.message.edit_text(
        text,
        reply_markup=kb(rows)
    )

    await callback.answer()


# ====================================
# УСЛОВИЯ УЧАСТИЯ
# ====================================

@router.callback_query(
    F.data.startswith("submissions:choose:")
)
async def show_terms(callback: CallbackQuery):

    contest_id = int(
        callback.data.rsplit(":", 1)[1]
    )

    contest = await get_contest(contest_id)

    if not contest or not is_open(contest):
        await callback.answer(
            "Конкурс недоступен",
            show_alert=True
        )
        return

    text = (
        f"🎮 {GAMES.get(contest['game_id'], 'Игра')}\n"
        f"🏆 {contest['title']}\n"
        f"💰 Призовой фонд: "
        f"{contest['prize_som']} сом\n"
        f"⏰ До: {short_date(contest['ends_at'])} "
        "(Бишкек)\n\n"

        f"🎯 Задание: {contest['task']}\n\n"
        f"⚖️ Критерии: {contest['criteria']}\n\n"

        "УСЛОВИЯ УЧАСТИЯ\n"
        "• Участие бесплатное, возраст от 18 лет.\n"
        "• Присылай только свою оригинальную "
        "игровую запись.\n"
        "• Ты разрешаешь SUPERQUEST неисключительно, "
        "без дополнительной оплаты использовать, "
        "монтировать и публиковать эту запись, "
        "в том числе в монетизируемых видео "
        "и рекламе.\n"
        "• Видео могут использоваться и без "
        "победы в конкурсе.\n"
        "• Права на саму игру остаются "
        "у правообладателя.\n\n"
        "Нажимая «Согласен», ты подтверждаешь "
        "эти условия."
    )

    await callback.message.edit_text(
        text,
        reply_markup=kb([
            [
                (
                    "✅ Мне 18+, согласен",
                    f"submissions:agree:{contest_id}"
                )
            ],
            [
                ("❌ Отмена", "menu:submissions")
            ]
        ])
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("submissions:agree:")
)
async def accept_terms(
    callback: CallbackQuery,
    state: FSMContext
):

    contest_id = int(
        callback.data.rsplit(":", 1)[1]
    )

    contest = await get_contest(contest_id)

    if not contest or not is_open(contest):
        await callback.answer(
            "Приём записей уже закрыт",
            show_alert=True
        )
        return

    await state.clear()

    await state.set_state(
        VideoSubmission.waiting_for_video
    )

    await state.update_data(
        contest_id=contest_id,
        terms_time=int(time.time())
    )

    await callback.message.edit_text(
        f"📤 Конкурс №{contest_id}\n\n"
        "Отправь игровую запись следующим сообщением.\n\n"
        "Поддерживается видео Telegram "
        "или видеофайл документом "
        "(MP4, MOV, MKV, WEBM).\n"
        "До 3 записей на конкурс.\n\n"
        "Для отмены нажми кнопку:",
        reply_markup=kb([
            [("❌ Отмена", "submissions:cancel")]
        ])
    )

    await callback.answer()


@router.callback_query(F.data == "submissions:cancel")
async def cancel_upload(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.clear()

    await callback.message.edit_text(
        "Отправка записи отменена.",
        reply_markup=back_to_menu()
    )

    await callback.answer()


@router.message(
    Command("cancel"),
    VideoSubmission.waiting_for_video
)
async def cancel_upload_command(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await message.answer(
        "Отправка отменена.",
        reply_markup=back_to_menu()
    )


# ====================================
# ПОЛУЧЕНИЕ ВИДЕО
# ====================================

@router.message(VideoSubmission.waiting_for_video)
async def receive_video(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    contest_id = data.get("contest_id")
    terms_time = data.get("terms_time")

    if not contest_id or not terms_time:

        await state.clear()

        await message.answer(
            "Сессия истекла. "
            "Начни заново через «Мои заявки»."
        )
        return

    media = None
    media_type = None

    if message.video:
        media = message.video
        media_type = "video"

    elif message.document:
        document = message.document

        filename = (
            document.file_name or ""
        ).lower()

        is_video = (
            (document.mime_type or "").startswith("video/")
            or filename.endswith(
                (".mp4", ".mov", ".mkv", ".webm")
            )
        )

        if is_video:
            media = document
            media_type = "document"

    if media is None:

        await message.answer(
            "Отправь видео или файл MP4/MOV/MKV/WEBM. "
            "Обычные изображения и текст не принимаются.\n"
            "Для отмены — /cancel"
        )
        return

    result, new_id = await add_submission(
        contest_id=contest_id,
        user_id=message.from_user.id,
        media_type=media_type,
        file_id=media.file_id,
        file_unique_id=media.file_unique_id,
        accepted_terms_at=terms_time
    )

    await state.clear()

    if result == "created":

        text = (
            f"✅ Заявка №{new_id} получена.\n"
            f"Конкурс №{contest_id}.\n"
            "Статус: ⏳ На проверке.\n\n"
            "Результат придёт уведомлением от бота."
        )

    else:

        messages = {
            "closed": (
                "Приём записей завершён "
                "или ещё не начался."
            ),
            "missing": "Конкурс не найден.",
            "limit": (
                "Ты уже отправил 3 записи "
                "на этот конкурс."
            ),
            "duplicate": (
                "Такая запись уже отправлялась "
                "на этот конкурс."
            )
        }

        text = (
            "❌ "
            + messages.get(
                result,
                "Не удалось сохранить заявку."
            )
        )

    await message.answer(
        text,
        reply_markup=back_to_menu()
    )


# ====================================
# ПРОСМОТР ЗАЯВКИ ИГРОКОМ
# ====================================

@router.callback_query(
    F.data.startswith("submissions:mine:")
)
async def view_my_submission(
    callback: CallbackQuery
):

    submission_id = int(
        callback.data.rsplit(":", 1)[1]
    )

    submission = await get_submission(
        submission_id
    )

    if (
        not submission
        or submission["user_id"] != callback.from_user.id
    ):

        await callback.answer(
            "Заявка не найдена",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        f"📹 Заявка №{submission_id}\n"
        f"🏆 Конкурс: "
        f"{submission['contest_title']}\n"
        f"📌 Статус: "
        f"{STATUS_LABELS[submission['status']]}\n"
        f"📅 Отправлено: "
        f"{short_date(submission['created_at'])}",
        reply_markup=kb([
            [
                (
                    "⬅️ К моим заявкам",
                    "menu:submissions"
                )
            ]
        ])
    )

    await callback.answer()


# ====================================
# АДМИН-ПАНЕЛЬ: ЗАЯВКИ
# ====================================

@router.message(Command("review"))
async def review_command(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ Нет доступа.")
        return

    await send_review_list(message)


async def send_review_list(message: Message):

    items = await get_pending_submissions()

    rows = [
        [
            (
                f"#{s['id']} · "
                f"{s['contest_title'][:25]}",
                f"submissions:admin:view:{s['id']}"
            )
        ]
        for s in items
    ]

    rows.append([
        ("🏠 Главное меню", "menu:home")
    ])

    await message.answer(
        "🛠 ПРОВЕРКА ЗАПИСЕЙ\n\n"
        + (
            "Выбери заявку:"
            if items
            else "Нет заявок на проверке."
        ),
        reply_markup=kb(rows)
    )


@router.callback_query(
    F.data == "submissions:admin:list"
)
async def review_list_callback(
    callback: CallbackQuery
):

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    items = await get_pending_submissions()

    rows = [
        [
            (
                f"#{s['id']} · "
                f"{s['contest_title'][:25]}",
                f"submissions:admin:view:{s['id']}"
            )
        ]
        for s in items
    ]

    rows.append([
        ("🏠 Главное меню", "menu:home")
    ])

    await callback.message.edit_text(
        "🛠 ПРОВЕРКА ЗАПИСЕЙ\n\n"
        + (
            "Выбери заявку:"
            if items
            else "Нет заявок на проверке."
        ),
        reply_markup=kb(rows)
    )

    await callback.answer()


# ====================================
# АДМИН: ДЕТАЛИ ЗАЯВКИ
# ====================================

@router.callback_query(
    F.data.startswith("submissions:admin:view:")
)
async def review_detail(
    callback: CallbackQuery
):

    if callback.from_user.id not in ADMIN_IDS:

        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    submission_id = int(
        callback.data.rsplit(":", 1)[1]
    )

    item = await get_submission(submission_id)

    if not item:

        await callback.answer(
            "Заявка не найдена",
            show_alert=True
        )
        return

    rows = [
        [
            (
                "▶️ Посмотреть видео",
                f"submissions:admin:video:{submission_id}"
            )
        ]
    ]

    if item["status"] == "pending":

        rows.extend([
            [
                (
                    "✅ Принять",
                    f"submissions:admin:approve:{submission_id}"
                )
            ],
            [
                (
                    "❌ Отклонить",
                    f"submissions:admin:reject:{submission_id}"
                )
            ]
        ])

    rows.append([
        ("⬅️ Назад", "submissions:admin:list")
    ])

    await callback.message.edit_text(
        f"📹 Заявка №{submission_id}\n"
        f"🏆 Конкурс: {item['contest_title']}\n"
        f"👤 Telegram ID игрока: {item['user_id']}\n"
        f"📌 Статус: {STATUS_LABELS[item['status']]}\n"
        f"📅 Отправлено: "
        f"{short_date(item['created_at'])}",
        reply_markup=kb(rows)
    )

    await callback.answer()


# ====================================
# АДМИН: ПРОСМОТР ВИДЕО
# ====================================

@router.callback_query(
    F.data.startswith("submissions:admin:video:")
)
async def preview_video(
    callback: CallbackQuery
):

    if callback.from_user.id not in ADMIN_IDS:

        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    submission_id = int(
        callback.data.rsplit(":", 1)[1]
    )

    item = await get_submission(submission_id)

    if not item:

        await callback.answer(
            "Заявка не найдена",
            show_alert=True
        )
        return

    try:

        if item["media_type"] == "video":

            await callback.bot.send_video(
                callback.from_user.id,
                item["file_id"]
            )

        else:

            await callback.bot.send_document(
                callback.from_user.id,
                item["file_id"]
            )

    except TelegramAPIError:

        await callback.answer(
            "Не удалось отправить видео",
            show_alert=True
        )
        return

    await callback.answer(
        "Видео отправлено отдельным сообщением"
    )


# ====================================
# АДМИН: РЕШЕНИЕ ПО ЗАЯВКЕ
# ====================================

@router.callback_query(
    F.data.startswith("submissions:admin:approve:")
)
@router.callback_query(
    F.data.startswith("submissions:admin:reject:")
)
async def moderate_submission(
    callback: CallbackQuery
):

    if callback.from_user.id not in ADMIN_IDS:

        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    submission_id = int(
        callback.data.rsplit(":", 1)[1]
    )

    action = callback.data.split(":")[2]

    status = (
        "approved"
        if action == "approve"
        else "rejected"
    )

    updated = await review_submission(
        submission_id,
        status,
        callback.from_user.id
    )

    if not updated:

        await callback.answer(
            "Заявка уже обработана или не найдена",
            show_alert=True
        )
        return

    item = await get_submission(submission_id)

    await callback.message.edit_text(
        f"Заявка №{submission_id}: "
        f"{STATUS_LABELS[status]}",
        reply_markup=kb([
            [
                (
                    "⬅️ К проверке",
                    "submissions:admin:list"
                )
            ]
        ])
    )

    try:

        await callback.bot.send_message(
            item["user_id"],
            f"📹 Заявка №{submission_id}: "
            f"{STATUS_LABELS[status]}\n\n"
            "Это результат проверки записи, "
            "а не итог конкурса."
        )

    except TelegramAPIError:
        pass

    await callback.answer("Статус обновлён")
