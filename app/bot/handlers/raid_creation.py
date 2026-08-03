import html
import logging
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.raid_creation import (
    get_raid_confirmation_keyboard,
    get_raid_creation_cancel_keyboard,
)
from app.bot.states.raid import RaidCreationStates
from app.config import load_config
from app.game_api.client import GameApiClient
from app.models.raid import Raid
from app.services.raid import (
    build_closed_raid_text,
    build_open_raid_text,
    extract_guild_member_count,
)
from app.storage.raid_storage import RaidStorage
from app.storage.settings_storage import SettingsStorage
from app.utils.damage import format_damage, parse_damage


router = Router(name="raid_creation")

raid_storage = RaidStorage()
settings_storage = SettingsStorage()

MOSCOW_TZ = ZoneInfo("Europe/Moscow")


async def is_allowed_admin(
    callback: CallbackQuery,
) -> bool:
    """
    Проверяет права пользователя.

    Создавать, завершать и отменять рейды могут:
    1. Владелец бота.
    2. Администратор Telegram-группы.
    3. Локальный администратор из settings.json.
    """

    config = load_config()
    user_id = callback.from_user.id

    if user_id == config.owner_telegram_id:
        return True

    if callback.message is None:
        return False

    if callback.message.chat.type == "private":
        return False

    chat_id = callback.message.chat.id

    if await settings_storage.is_local_admin(
        chat_id=chat_id,
        telegram_user_id=user_id,
    ):
        return True

    try:
        member = await callback.bot.get_chat_member(
            chat_id=chat_id,
            user_id=user_id,
        )
    except Exception:
        logging.exception(
            "Не удалось проверить права администратора"
        )
        return False

    return member.status in {
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.ADMINISTRATOR,
    }


def parse_date(
    value: str,
) -> str | None:
    """
    Проверяет дату в формате ДД.ММ.ГГГГ.
    """

    try:
        parsed = datetime.strptime(
            value.strip(),
            "%d.%m.%Y",
        )
    except ValueError:
        return None

    return parsed.strftime("%d.%m.%Y")


def parse_time(
    value: str,
) -> str | None:
    """
    Проверяет время в формате ЧЧ:ММ.
    """

    try:
        parsed = datetime.strptime(
            value.strip(),
            "%H:%M",
        )
    except ValueError:
        return None

    return parsed.strftime("%H:%M")


def build_raid_datetime(
    raid_date: str,
    start_time: str,
) -> datetime:
    """
    Объединяет дату и время рейда.

    Результат всегда имеет часовой пояс Москвы.
    """

    return datetime.strptime(
        f"{raid_date} {start_time}",
        "%d.%m.%Y %H:%M",
    ).replace(
        tzinfo=MOSCOW_TZ,
    )


def is_raid_datetime_in_future(
    raid_date: str,
    start_time: str,
) -> bool:
    """
    Проверяет, что дата и время рейда ещё не прошли.
    """

    raid_datetime = build_raid_datetime(
        raid_date=raid_date,
        start_time=start_time,
    )

    current_moscow_time = datetime.now(
        MOSCOW_TZ
    )

    return raid_datetime > current_moscow_time


async def get_guild_member_count() -> int:
    """
    Получает текущее количество участников бригады.
    """

    api_client = GameApiClient(
        config=load_config()
    )

    try:
        guild_status = (
            await api_client.get_guild_status()
        )

        return extract_guild_member_count(
            guild_status
        )

    finally:
        await api_client.close()


async def pin_raid_message(
    callback: CallbackQuery,
    raid: Raid,
) -> None:
    """
    Закрепляет основное сообщение рейда.

    Ошибка закрепления не отменяет создание рейда.
    """

    if raid.announcement_message_id is None:
        return

    try:
        await callback.bot.pin_chat_message(
            chat_id=raid.chat_id,
            message_id=raid.announcement_message_id,
            disable_notification=True,
        )

    except Exception:
        logging.exception(
            "Не удалось закрепить сообщение рейда"
        )


async def unpin_raid_message(
    callback: CallbackQuery,
    raid: Raid,
) -> None:
    """
    Снимает закрепление с основного сообщения рейда.

    Ошибка снятия закрепления не мешает
    завершению или отмене рейда.
    """

    if raid.announcement_message_id is None:
        return

    try:
        await callback.bot.unpin_chat_message(
            chat_id=raid.chat_id,
            message_id=raid.announcement_message_id,
        )

    except Exception:
        logging.exception(
            "Не удалось снять закрепление "
            "с сообщения рейда"
        )


@router.callback_query(
    F.data == "admin:raid:create"
)
async def start_raid_creation(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Начинает пошаговое создание рейда.
    """

    if callback.message is None:
        return

    if callback.message.chat.type == "private":
        await callback.answer(
            "Открывать рейд нужно в группе.",
            show_alert=True,
        )
        return

    if not await is_allowed_admin(callback):
        await callback.answer(
            "Недостаточно прав.",
            show_alert=True,
        )
        return

    chat_id = callback.message.chat.id

    active_raid = await raid_storage.get_active_raid(
        chat_id
    )

    if active_raid is not None:
        await callback.answer(
            "В этом чате уже открыт рейд.",
            show_alert=True,
        )
        return

    chat_settings = await settings_storage.get_chat(
        chat_id
    )

    if (
        chat_settings is None
        or chat_settings.topics.raids is None
    ):
        await callback.answer(
            "Сначала настрой ветку рейдов "
            "через команду /setup.",
            show_alert=True,
        )
        return

    await state.clear()

    await state.update_data(
        chat_id=chat_id,
        thread_id=chat_settings.topics.raids,
        created_by=callback.from_user.id,
    )

    await state.set_state(
        RaidCreationStates.waiting_for_date
    )

    await callback.answer()

    current_moscow_time = datetime.now(
        MOSCOW_TZ
    )

    await callback.message.answer(
        text=(
            "📅 <b>Введите дату рейда</b>\n\n"
            "Формат:\n"
            "<code>05.08.2026</code>\n\n"
            "Все даты и время указываются по МСК.\n\n"
            f"Сейчас по МСК:\n"
            f"<b>"
            f"{current_moscow_time.strftime('%d.%m.%Y %H:%M')}"
            f"</b>"
        ),
        reply_markup=(
            get_raid_creation_cancel_keyboard()
        ),
    )


@router.message(
    RaidCreationStates.waiting_for_date
)
async def receive_raid_date(
    message: Message,
    state: FSMContext,
) -> None:
    """
    Получает дату рейда.
    """

    raid_date = parse_date(
        message.text or ""
    )

    if raid_date is None:
        await message.answer(
            text=(
                "❌ Неверный формат даты.\n\n"
                "Введите дату так:\n"
                "<code>05.08.2026</code>"
            ),
            reply_markup=(
                get_raid_creation_cancel_keyboard()
            ),
        )
        return

    parsed_date = datetime.strptime(
        raid_date,
        "%d.%m.%Y",
    ).date()

    current_moscow_date = datetime.now(
        MOSCOW_TZ
    ).date()

    if parsed_date < current_moscow_date:
        await message.answer(
            text=(
                "❌ Нельзя создать рейд "
                "на прошедшую дату.\n\n"
                f"Сегодня по МСК:\n"
                f"<b>"
                f"{current_moscow_date.strftime('%d.%m.%Y')}"
                f"</b>\n\n"
                "Введите сегодняшнюю или будущую дату."
            ),
            reply_markup=(
                get_raid_creation_cancel_keyboard()
            ),
        )
        return

    await state.update_data(
        raid_date=raid_date
    )

    await state.set_state(
        RaidCreationStates.waiting_for_time
    )

    await message.answer(
        text=(
            "🕒 <b>Введите время начала</b>\n\n"
            "Формат:\n"
            "<code>20:00</code>\n\n"
            "Время указывается по МСК."
        ),
        reply_markup=(
            get_raid_creation_cancel_keyboard()
        ),
    )


@router.message(
    RaidCreationStates.waiting_for_time
)
async def receive_raid_time(
    message: Message,
    state: FSMContext,
) -> None:
    """
    Получает время начала и проверяет,
    что рейд ещё не прошёл.
    """

    start_time = parse_time(
        message.text or ""
    )

    if start_time is None:
        await message.answer(
            text=(
                "❌ Неверный формат времени.\n\n"
                "Введите время так:\n"
                "<code>20:00</code>"
            ),
            reply_markup=(
                get_raid_creation_cancel_keyboard()
            ),
        )
        return

    data = await state.get_data()

    raid_date = str(
        data.get("raid_date") or ""
    )

    if not raid_date:
        await state.clear()

        await message.answer(
            "❌ Данные даты потеряны. "
            "Начните создание рейда заново."
        )
        return

    if not is_raid_datetime_in_future(
        raid_date=raid_date,
        start_time=start_time,
    ):
        current_moscow_time = datetime.now(
            MOSCOW_TZ
        )

        await message.answer(
            text=(
                "❌ Нельзя создать рейд "
                "на прошедшее время.\n\n"
                f"Сейчас по МСК:\n"
                f"<b>"
                f"{current_moscow_time.strftime('%d.%m.%Y %H:%M')}"
                f"</b>\n\n"
                "Введите будущее время."
            ),
            reply_markup=(
                get_raid_creation_cancel_keyboard()
            ),
        )
        return

    await state.update_data(
        start_time=start_time
    )

    await state.set_state(
        RaidCreationStates.waiting_for_minimum_damage
    )

    await message.answer(
        text=(
            "🎯 <b>Введите минимальный урон</b>\n\n"
            "Примеры:\n"
            "<code>50кк</code>\n"
            "<code>1,5ккк</code>\n"
            "<code>750м</code>"
        ),
        reply_markup=(
            get_raid_creation_cancel_keyboard()
        ),
    )


@router.message(
    RaidCreationStates.waiting_for_minimum_damage
)
async def receive_minimum_damage(
    message: Message,
    state: FSMContext,
) -> None:
    """
    Получает минимальный урон рейда.
    """

    minimum_damage = parse_damage(
        message.text or ""
    )

    if minimum_damage is None:
        await message.answer(
            text=(
                "❌ Не удалось распознать урон.\n\n"
                "Примеры:\n"
                "<code>50кк</code>\n"
                "<code>50000000</code>\n"
                "<code>1,5ккк</code>"
            ),
            reply_markup=(
                get_raid_creation_cancel_keyboard()
            ),
        )
        return

    await state.update_data(
        minimum_damage=minimum_damage
    )

    data = await state.get_data()

    raid_date = str(
        data.get("raid_date") or ""
    )

    start_time = str(
        data.get("start_time") or ""
    )

    if not is_raid_datetime_in_future(
        raid_date=raid_date,
        start_time=start_time,
    ):
        await state.set_state(
            RaidCreationStates.waiting_for_time
        )

        current_moscow_time = datetime.now(
            MOSCOW_TZ
        )

        await message.answer(
            text=(
                "❌ Пока вы вводили данные, "
                "указанное время уже прошло.\n\n"
                f"Сейчас по МСК:\n"
                f"<b>"
                f"{current_moscow_time.strftime('%d.%m.%Y %H:%M')}"
                f"</b>\n\n"
                "Введите новое время начала."
            ),
            reply_markup=(
                get_raid_creation_cancel_keyboard()
            ),
        )
        return

    await state.set_state(
        RaidCreationStates.waiting_for_confirmation
    )

    await message.answer(
        text=(
            "⚔️ <b>Новый рейд</b>\n\n"
            f"📅 <b>Дата:</b> "
            f"{html.escape(raid_date)}\n"
            f"🕒 <b>Начало:</b> "
            f"{html.escape(start_time)} МСК\n"
            f"🎯 <b>Минимальный урон:</b> "
            f"{format_damage(minimum_damage)}\n\n"
            "Опубликовать рейд?"
        ),
        reply_markup=(
            get_raid_confirmation_keyboard()
        ),
    )


@router.callback_query(
    RaidCreationStates.waiting_for_confirmation,
    F.data == "raid:create:confirm",
)
async def confirm_raid_creation(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Публикует и закрепляет объявление рейда.
    """

    if callback.message is None:
        return

    data = await state.get_data()

    raid_date = str(
        data.get("raid_date") or ""
    )

    start_time = str(
        data.get("start_time") or ""
    )

    if not is_raid_datetime_in_future(
        raid_date=raid_date,
        start_time=start_time,
    ):
        current_moscow_time = datetime.now(
            MOSCOW_TZ
        )

        await callback.answer(
            "Дата или время рейда уже прошли.",
            show_alert=True,
        )

        await state.set_state(
            RaidCreationStates.waiting_for_time
        )

        await callback.message.edit_text(
            text=(
                "❌ <b>Рейд не опубликован</b>\n\n"
                "Указанная дата или время уже прошли.\n\n"
                f"Сейчас по МСК:\n"
                f"<b>"
                f"{current_moscow_time.strftime('%d.%m.%Y %H:%M')}"
                f"</b>\n\n"
                "Введите новое время начала."
            ),
            reply_markup=(
                get_raid_creation_cancel_keyboard()
            ),
        )
        return

    await callback.answer(
        "Публикую рейд..."
    )

    try:
        total_members = (
            await get_guild_member_count()
        )

        raid = Raid(
            raid_id=uuid4().hex,
            chat_id=int(data["chat_id"]),
            thread_id=int(data["thread_id"]),
            raid_date=raid_date,
            start_time=start_time,
            minimum_damage=int(
                data["minimum_damage"]
            ),
            total_guild_members=total_members,
            created_by=int(
                data["created_by"]
            ),
            created_at=datetime.now(
                MOSCOW_TZ
            ).isoformat(),
        )

        announcement = (
            await callback.bot.send_message(
                chat_id=raid.chat_id,
                message_thread_id=raid.thread_id,
                text=build_open_raid_text(
                    raid
                ),
            )
        )

        raid.announcement_message_id = (
            announcement.message_id
        )

        await raid_storage.save_active_raid(
            raid
        )

        await pin_raid_message(
            callback=callback,
            raid=raid,
        )

        await state.clear()

        await callback.message.edit_text(
            text=(
                "✅ <b>Рейд опубликован</b>\n\n"
                f"📅 Дата: {raid.raid_date}\n"
                f"🕒 Начало: {raid.start_time} МСК\n"
                f"🎯 Минимальный урон: "
                f"{format_damage(raid.minimum_damage)}\n\n"
                "Приём заявок открыт "
                "в ветке рейдов.\n\n"
                "Сообщение рейда закреплено."
            )
        )

    except Exception as error:
        logging.exception(
            "Ошибка публикации рейда"
        )

        await callback.message.answer(
            text=(
                "❌ Не удалось опубликовать рейд.\n\n"
                f"<code>"
                f"{html.escape(str(error))}"
                f"</code>"
            )
        )


@router.callback_query(
    F.data == "raid:create:cancel"
)
async def cancel_raid_creation(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Отменяет незавершённый диалог создания.
    """

    await state.clear()

    await callback.answer(
        "Создание рейда отменено."
    )

    if callback.message is not None:
        await callback.message.edit_text(
            "❌ Создание рейда отменено."
        )


@router.callback_query(
    F.data == "admin:raid:finish"
)
async def finish_active_raid(
    callback: CallbackQuery,
) -> None:
    """
    Завершает активный рейд,
    обновляет объявление и снимает закрепление.
    """

    if callback.message is None:
        return

    if not await is_allowed_admin(
        callback
    ):
        await callback.answer(
            "Недостаточно прав.",
            show_alert=True,
        )
        return

    raid = await raid_storage.close_active_raid(
        callback.message.chat.id,
        datetime.now(
            MOSCOW_TZ
        ).isoformat(),
    )

    if raid is None:
        await callback.answer(
            "Открытый рейд не найден.",
            show_alert=True,
        )
        return

    if raid.announcement_message_id is not None:
        try:
            await callback.bot.edit_message_text(
                chat_id=raid.chat_id,
                message_id=(
                    raid.announcement_message_id
                ),
                text=build_closed_raid_text(
                    raid
                ),
            )

        except Exception:
            logging.exception(
                "Не удалось обновить сообщение "
                "завершённого рейда"
            )

    await unpin_raid_message(
        callback=callback,
        raid=raid,
    )

    await callback.answer(
        "Рейд завершён."
    )

    await callback.message.edit_text(
        text=(
            "🏁 <b>Рейд завершён</b>\n\n"
            f"💥 Итоговый урон: "
            f"{format_damage(raid.total_damage)}\n"
            f"👥 Участников: "
            f"{raid.participants_count}"
            f" / "
            f"{raid.total_guild_members}"
        )
    )


@router.callback_query(
    F.data == "admin:raid:cancel"
)
async def cancel_active_raid(
    callback: CallbackQuery,
) -> None:
    """
    Отменяет активный рейд
    и снимает закрепление.
    """

    if callback.message is None:
        return

    if not await is_allowed_admin(
        callback
    ):
        await callback.answer(
            "Недостаточно прав.",
            show_alert=True,
        )
        return

    raid = await raid_storage.cancel_active_raid(
        callback.message.chat.id
    )

    if raid is None:
        await callback.answer(
            "Открытый рейд не найден.",
            show_alert=True,
        )
        return

    if raid.announcement_message_id is not None:
        try:
            await callback.bot.edit_message_text(
                chat_id=raid.chat_id,
                message_id=(
                    raid.announcement_message_id
                ),
                text=(
                    "❌ <b>РЕЙД ОТМЕНЁН</b>\n\n"
                    f"📅 Дата: {raid.raid_date}\n"
                    f"🕒 Начало: "
                    f"{raid.start_time} МСК"
                ),
            )

        except Exception:
            logging.exception(
                "Не удалось обновить сообщение "
                "отменённого рейда"
            )

    await unpin_raid_message(
        callback=callback,
        raid=raid,
    )

    await callback.answer(
        "Рейд отменён."
    )

    await callback.message.edit_text(
        "❌ Рейд отменён."
    )
