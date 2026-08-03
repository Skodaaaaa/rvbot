from aiogram import Router
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command
from aiogram.types import Message

from app.config import load_config


router = Router(name="info")


async def check_telegram_admin(
    message: Message,
) -> bool:
    """
    Проверяет, является ли пользователь
    администратором или владельцем Telegram-чата.
    """

    if message.from_user is None:
        return False

    if message.chat.type == "private":
        return True

    member = await message.bot.get_chat_member(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
    )

    return member.status in {
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.ADMINISTRATOR,
    }


@router.message(Command("id"))
async def id_command(message: Message) -> None:
    config = load_config()

    user_id = (
        message.from_user.id
        if message.from_user is not None
        else None
    )

    thread_id = message.message_thread_id

    is_owner = (
        user_id is not None
        and user_id == config.owner_telegram_id
    )

    try:
        is_chat_admin = await check_telegram_admin(
            message
        )
    except Exception:
        is_chat_admin = False

    user_status_parts: list[str] = []

    if is_owner:
        user_status_parts.append(
            "👑 Владелец бота"
        )

    if is_chat_admin:
        user_status_parts.append(
            "🔑 Администратор Telegram-чата"
        )

    if not user_status_parts:
        user_status_parts.append(
            "👤 Обычный пользователь"
        )

    user_status = "\n".join(
        user_status_parts
    )

    thread_text = (
        str(thread_id)
        if thread_id is not None
        else "нет — сообщение отправлено не в отдельной ветке"
    )

    text = (
        "ℹ️ <b>Информация</b>\n\n"
        f"👤 <b>Ваш Telegram ID:</b>\n"
        f"<code>{user_id}</code>\n\n"
        f"💬 <b>Chat ID:</b>\n"
        f"<code>{message.chat.id}</code>\n\n"
        f"🧵 <b>Thread ID:</b>\n"
        f"<code>{thread_text}</code>\n\n"
        f"📂 <b>Тип чата:</b>\n"
        f"<code>{message.chat.type}</code>\n\n"
        f"🏷 <b>Название чата:</b>\n"
        f"{message.chat.title or 'Личная переписка'}\n\n"
        f"<b>Ваш статус:</b>\n"
        f"{user_status}"
    )

    await message.answer(
        text=text,
    )