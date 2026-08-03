import html
from typing import Any

from app.models.raid import Raid
from app.utils.damage import format_damage


def find_guild_member_by_telegram_id(
    guild_status: Any,
    telegram_user_id: int,
) -> dict[str, Any] | None:
    if not isinstance(guild_status, dict):
        return None

    members = guild_status.get("members", [])
    if not isinstance(members, list):
        return None

    for member in members:
        if not isinstance(member, dict):
            continue

        try:
            game_user_id = int(member.get("userId"))
        except (TypeError, ValueError):
            continue

        if game_user_id == telegram_user_id:
            return member

    return None


def extract_guild_member_count(guild_status: Any) -> int:
    if not isinstance(guild_status, dict):
        return 0

    guild = guild_status.get("guild")
    if isinstance(guild, dict):
        try:
            return int(guild.get("memberCount", 0))
        except (TypeError, ValueError):
            pass

    members = guild_status.get("members", [])
    return len(members) if isinstance(members, list) else 0


def build_open_raid_text(raid: Raid) -> str:
    return (
        "⚔️ <b>РЕЙД ОТКРЫТ</b>\n\n"
        f"📅 <b>Дата:</b> {html.escape(raid.raid_date)}\n"
        f"🕒 <b>Начало:</b> {html.escape(raid.start_time)}\n"
        f"🎯 <b>Минимальный урон:</b> {format_damage(raid.minimum_damage)}\n\n"
        "━━━━━━━━━━━━━━━━\n\n"
        f"💥 <b>Общий заявленный урон:</b>\n{format_damage(raid.total_damage)}\n\n"
        f"👥 <b>Заявили:</b>\n{raid.participants_count} / {raid.total_guild_members}\n\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "Напишите свой урон отдельным сообщением.\n\n"
        "<b>Примеры:</b>\n"
        "<code>50кк</code>\n"
        "<code>50000000</code>\n"
        "<code>1,5ккк</code>\n"
        "<code>750м</code>"
    )


def build_closed_raid_text(raid: Raid) -> str:
    return (
        "🏁 <b>РЕЙД ЗАВЕРШЁН</b>\n\n"
        f"📅 <b>Дата:</b> {html.escape(raid.raid_date)}\n"
        f"🕒 <b>Начало:</b> {html.escape(raid.start_time)}\n"
        f"🎯 <b>Минимальный урон:</b> {format_damage(raid.minimum_damage)}\n\n"
        "━━━━━━━━━━━━━━━━\n\n"
        f"💥 <b>Итоговый урон:</b>\n{format_damage(raid.total_damage)}\n\n"
        f"👥 <b>Заявили:</b>\n{raid.participants_count} / {raid.total_guild_members}"
    )
