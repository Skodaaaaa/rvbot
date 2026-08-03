import html
import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.types import Message, ReactionTypeEmoji

from app.config import load_config
from app.game_api.client import GameApiClient
from app.models.raid import RaidParticipant
from app.services.raid import build_open_raid_text, find_guild_member_by_telegram_id
from app.storage.raid_storage import RaidStorage
from app.storage.settings_storage import SettingsStorage
from app.utils.damage import format_damage, parse_damage


router = Router(name="raid_damage")
raid_storage = RaidStorage()
settings_storage = SettingsStorage()


async def set_reaction(message: Message, emoji: str) -> None:
    try:
        await message.bot.set_message_reaction(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reaction=[ReactionTypeEmoji(emoji=emoji)],
        )
    except Exception:
        logging.exception("Не удалось поставить реакцию %s", emoji)


async def replace_old_reaction(
    message: Message,
    old_message_id: int,
    emoji: str,
) -> None:
    try:
        await message.bot.set_message_reaction(
            chat_id=message.chat.id,
            message_id=old_message_id,
            reaction=[ReactionTypeEmoji(emoji=emoji)],
        )
    except Exception:
        logging.exception("Не удалось заменить реакцию старой заявки")


@router.message(F.text)
async def receive_raid_damage(message: Message) -> None:
    if message.from_user is None or message.from_user.is_bot:
        return
    if message.chat.type == "private":
        return

    chat_settings = await settings_storage.get_chat(message.chat.id)
    if chat_settings is None or chat_settings.topics.raids is None:
        return
    if message.message_thread_id != chat_settings.topics.raids:
        return

    damage = parse_damage(message.text or "")
    if damage is None:
        return

    raid = await raid_storage.get_active_raid(message.chat.id)
    if raid is None or raid.thread_id != message.message_thread_id:
        return

    api_client = GameApiClient(config=load_config())
    try:
        guild_status = await api_client.get_guild_status()
        member = find_guild_member_by_telegram_id(
            guild_status,
            message.from_user.id,
        )
    except Exception as error:
        logging.exception("Не удалось определить участника бригады")
        await message.reply(
            "❌ Не удалось проверить ваш игровой профиль.\n\n"
            f"<code>{html.escape(str(error))}</code>"
        )
        return
    finally:
        await api_client.close()

    if member is None:
        await set_reaction(message, "❌")
        await message.reply(
            "❌ Ваш Telegram ID не найден среди участников бригады."
        )
        return

    nickname = str(member.get("nickname") or f"Игрок {message.from_user.id}")
    game_user_id = int(member.get("userId"))

    if damage < raid.minimum_damage:
        await set_reaction(message, "❌")
        await message.reply(
            f"❌ <b>{html.escape(nickname)}</b>, заявка не принята.\n\n"
            f"Ваш урон: {format_damage(damage)}\n"
            f"Минимум: {format_damage(raid.minimum_damage)}"
        )
        return

    participant_key = str(message.from_user.id)
    previous = raid.participants.get(participant_key)

    if previous is not None:
        await replace_old_reaction(message, previous.message_id, "♻️")

    raid.participants[participant_key] = RaidParticipant(
        telegram_user_id=message.from_user.id,
        game_user_id=game_user_id,
        nickname=nickname,
        damage=damage,
        message_id=message.message_id,
        updated_at=datetime.now().isoformat(),
    )

    if raid.last_service_message_id is not None:
        try:
            await message.bot.delete_message(
                chat_id=raid.chat_id,
                message_id=raid.last_service_message_id,
            )
        except Exception:
            logging.exception("Не удалось удалить предыдущее служебное сообщение")

    await set_reaction(message, "✅")

    if raid.announcement_message_id is not None:
        try:
            await message.bot.edit_message_text(
                chat_id=raid.chat_id,
                message_id=raid.announcement_message_id,
                text=build_open_raid_text(raid),
            )
        except Exception:
            logging.exception("Не удалось обновить главное сообщение рейда")

    action_text = "обновлён" if previous is not None else "принят"
    service_message = await message.reply(
        f"✅ <b>{html.escape(nickname)}</b>, ваш урон {action_text}.\n\n"
        f"Ваш урон: {format_damage(damage)}\n"
        f"Общий урон: {format_damage(raid.total_damage)}\n"
        f"Участников: {raid.participants_count} / {raid.total_guild_members}"
    )

    raid.last_service_message_id = service_message.message_id
    await raid_storage.save_active_raid(raid)
