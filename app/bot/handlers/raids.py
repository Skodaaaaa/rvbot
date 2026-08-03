from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.handlers.menu import edit_callback_message
from app.bot.keyboards.raid_menu import get_raid_back_keyboard
from app.services.raid import build_closed_raid_text, build_open_raid_text
from app.storage.raid_storage import RaidStorage
from app.utils.damage import format_damage


router = Router(name="raids")
raid_storage = RaidStorage()


@router.callback_query(F.data == "raids:current")
async def current_raid_callback(callback: CallbackQuery) -> None:
    if callback.message is None:
        return

    raid = await raid_storage.get_active_raid(callback.message.chat.id)
    text = (
        build_open_raid_text(raid)
        if raid is not None
        else "⚔️ <b>Текущий рейд</b>\n\nОткрытый рейд отсутствует."
    )

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_raid_back_keyboard(),
    )


@router.callback_query(F.data == "raids:participants")
async def raid_participants_callback(callback: CallbackQuery) -> None:
    if callback.message is None:
        return

    raid = await raid_storage.get_active_raid(callback.message.chat.id)
    if raid is None:
        text = "👥 <b>Участники рейда</b>\n\nОткрытый рейд отсутствует."
    elif not raid.participants:
        text = "👥 <b>Участники рейда</b>\n\nЗаявок пока нет."
    else:
        participants = sorted(
            raid.participants.values(),
            key=lambda item: item.damage,
            reverse=True,
        )
        lines = ["👥 <b>Участники рейда</b>", ""]
        for index, participant in enumerate(participants, start=1):
            lines.append(
                f"{index}. {participant.nickname} — {format_damage(participant.damage)}"
            )
        text = "\n".join(lines)

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_raid_back_keyboard(),
    )


@router.callback_query(F.data == "raids:history")
async def raid_history_callback(callback: CallbackQuery) -> None:
    if callback.message is None:
        return

    history = await raid_storage.get_history(callback.message.chat.id)
    if not history:
        text = "📜 <b>История рейдов</b>\n\nЗавершённых рейдов пока нет."
    else:
        lines = ["📜 <b>История рейдов</b>", ""]
        for index, raid in enumerate(history[:10], start=1):
            lines.append(
                f"{index}. {raid.raid_date} {raid.start_time} — "
                f"{format_damage(raid.total_damage)} — "
                f"{raid.participants_count}/{raid.total_guild_members}"
            )
        text = "\n".join(lines)

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_raid_back_keyboard(),
    )
