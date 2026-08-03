from aiogram import F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.setup import get_setup_keyboard
from app.config import load_config
from app.storage.settings_storage import SettingsStorage


router = Router(name="setup")

settings_storage = SettingsStorage()


async def is_allowed_admin(
    chat_id: int,
    telegram_user_id: int,
    bot,
) -> bool:
    """
    Разрешает настройку:

    1. Владельцу бота из .env.
    2. Администратору Telegram-чата.
    3. Локальному администратору из settings.json.
    """

    config = load_config()

    if telegram_user_id == config.owner_telegram_id:
        return True

    if await settings_storage.is_local_admin(
        chat_id=chat_id,
        telegram_user_id=telegram_user_id,
    ):
        return True

    try:
        member = await bot.get_chat_member(
            chat_id=chat_id,
            user_id=telegram_user_id,
        )
    except Exception:
        return False

    return member.status in {
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.ADMINISTRATOR,
    }


def format_topic_id(
    topic_id: int | None,
) -> str:
    if topic_id is None:
        return "не настроена"

    return f"<code>{topic_id}</code>"


async def build_settings_text(
    chat_id: int,
    chat_title: str | None,
) -> str:
    chat_settings = (
        await settings_storage.get_or_create_chat(
            chat_id=chat_id,
            title=chat_title,
        )
    )

    return (
        "⚙️ <b>Настройки чата</b>\n\n"
        f"💬 <b>Chat ID:</b>\n"
        f"<code>{chat_settings.chat_id}</code>\n\n"
        f"⚔️ <b>Ветка рейдов:</b>\n"
        f"{format_topic_id(chat_settings.topics.raids)}\n\n"
        f"🏕 <b>Ветка лагерей:</b>\n"
        f"{format_topic_id(chat_settings.topics.camps)}\n\n"
        f"📢 <b>Ветка объявлений:</b>\n"
        f"{format_topic_id(chat_settings.topics.announcements)}\n\n"
        "Чтобы привязать ветку, вызови команду "
        "<code>/setup</code> именно внутри нужной темы, "
        "а затем нажми соответствующую кнопку."
    )


@router.message(Command("setup"))
async def setup_command(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    if message.chat.type == "private":
        await message.answer(
            "Команда <code>/setup</code> предназначена "
            "для группового чата.\n\n"
            "Добавь бота в группу и вызови команду там."
        )
        return

    allowed = await is_allowed_admin(
        chat_id=message.chat.id,
        telegram_user_id=message.from_user.id,
        bot=message.bot,
    )

    if not allowed:
        await message.answer(
            "⛔ Эта команда доступна только "
            "владельцу бота или администратору чата."
        )
        return

    await settings_storage.get_or_create_chat(
        chat_id=message.chat.id,
        title=message.chat.title,
    )

    text = await build_settings_text(
        chat_id=message.chat.id,
        chat_title=message.chat.title,
    )

    await message.answer(
        text=text,
        reply_markup=get_setup_keyboard(),
    )


@router.callback_query(
    F.data.startswith("setup:topic:")
)
async def set_topic_callback(
    callback: CallbackQuery,
) -> None:
    if callback.from_user is None:
        return

    if callback.message is None:
        await callback.answer(
            "Не удалось определить сообщение.",
            show_alert=True,
        )
        return

    chat = callback.message.chat

    if chat.type == "private":
        await callback.answer(
            "Настройка веток работает только в группе.",
            show_alert=True,
        )
        return

    allowed = await is_allowed_admin(
        chat_id=chat.id,
        telegram_user_id=callback.from_user.id,
        bot=callback.bot,
    )

    if not allowed:
        await callback.answer(
            "Недостаточно прав.",
            show_alert=True,
        )
        return

    thread_id = callback.message.message_thread_id

    if thread_id is None:
        await callback.answer(
            "Эта кнопка нажата не внутри отдельной ветки.\n"
            "Открой нужную тему, вызови /setup "
            "и нажми кнопку там.",
            show_alert=True,
        )
        return

    callback_data = callback.data or ""
    topic_type = callback_data.rsplit(
        ":",
        maxsplit=1,
    )[-1]

    allowed_topic_types = {
        "raids",
        "camps",
        "announcements",
    }

    if topic_type not in allowed_topic_types:
        await callback.answer(
            "Неизвестный тип ветки.",
            show_alert=True,
        )
        return

    await settings_storage.set_topic(
        chat_id=chat.id,
        topic_type=topic_type,
        thread_id=thread_id,
        title=chat.title,
    )

    topic_names = {
        "raids": "рейдов",
        "camps": "лагерей",
        "announcements": "объявлений",
    }

    await callback.answer(
        "Настройка сохранена.",
    )

    text = (
        "✅ <b>Ветка успешно привязана</b>\n\n"
        f"Тип: <b>{topic_names[topic_type]}</b>\n"
        f"Thread ID: <code>{thread_id}</code>"
    )

    await callback.message.answer(
        text=text,
    )


@router.callback_query(
    F.data == "setup:show"
)
async def show_settings_callback(
    callback: CallbackQuery,
) -> None:
    if callback.message is None:
        return

    chat = callback.message.chat

    if chat.type == "private":
        await callback.answer(
            "Настройки доступны только в группе.",
            show_alert=True,
        )
        return

    allowed = await is_allowed_admin(
        chat_id=chat.id,
        telegram_user_id=callback.from_user.id,
        bot=callback.bot,
    )

    if not allowed:
        await callback.answer(
            "Недостаточно прав.",
            show_alert=True,
        )
        return

    text = await build_settings_text(
        chat_id=chat.id,
        chat_title=chat.title,
    )

    await callback.answer()

    await callback.message.answer(
        text=text,
        reply_markup=get_setup_keyboard(),
    )