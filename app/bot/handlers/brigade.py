import html
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from app.bot.keyboards.brigade_menu import (
    get_brigade_back_keyboard,
    get_player_card_keyboard,
    get_players_catalog_keyboard,
)
from app.config import load_config
from app.game_api.client import GameApiClient
from app.game_api.exceptions import GameApiError
from app.services.guild import GuildService


router = Router(name="brigade")


def format_number(
    value: int | None,
) -> str:
    """
    23169987 -> 23 169 987
    """

    if value is None:
        return "0"

    return f"{value:,}".replace(",", " ")


async def edit_message(
    callback: CallbackQuery,
    text: str,
    reply_markup,
) -> None:
    """
    Редактирует текущее сообщение.
    """

    if callback.message is None:
        return

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=reply_markup,
        )
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error):
            raise


def create_guild_service() -> tuple[
    GameApiClient,
    GuildService,
]:
    """
    Создаёт игровой API-клиент.
    """

    config = load_config()

    api_client = GameApiClient(
        config=config,
    )

    service = GuildService(
        api_client=api_client,
    )

    return api_client, service


async def show_error(
    callback: CallbackQuery,
    error: Exception,
) -> None:
    """
    Показывает безопасную ошибку.
    """

    if isinstance(error, GameApiError):
        status = (
            str(error.status)
            if error.status is not None
            else "неизвестен"
        )

        message = error.message

        logging.error(
            "Ошибка игрового API. HTTP=%s, payload=%r",
            status,
            error.payload,
            exc_info=True,
        )
    else:
        status = "неизвестен"
        message = str(error)

        logging.exception(
            "Ошибка раздела бригады"
        )

    text = (
        "❌ <b>Не удалось загрузить данные</b>\n\n"
        f"HTTP-статус: "
        f"<code>{html.escape(status)}</code>\n\n"
        f"Ошибка:\n"
        f"<code>{html.escape(message)}</code>"
    )

    await edit_message(
        callback=callback,
        text=text,
        reply_markup=get_brigade_back_keyboard(),
    )


@router.callback_query(
    F.data == "brigade:info"
)
async def brigade_info_callback(
    callback: CallbackQuery,
) -> None:
    await callback.answer(
        "Загружаю информацию..."
    )

    api_client, service = create_guild_service()

    try:
        payload = await service.get_guild_status()
        info = service.extract_guild_info(
            payload
        )

        text = (
            f"👥 <b>{html.escape(info['name'])}</b>\n\n"
            f"⭐ <b>Уровень:</b> "
            f"{format_number(info['level'])}\n\n"
            f"📈 <b>Опыт:</b> "
            f"{format_number(info['experience'])}"
            f" / "
            f"{format_number(info['experience_to_next'])}\n\n"
            f"👤 <b>Участники:</b> "
            f"{format_number(info['member_count'])}"
            f" / "
            f"{format_number(info['max_members'])}\n\n"
            f"👑 <b>Лидер:</b> "
            f"{html.escape(info['leader_nickname'])}"
        )

        await edit_message(
            callback=callback,
            text=text,
            reply_markup=get_brigade_back_keyboard(),
        )

    except Exception as error:
        await show_error(
            callback=callback,
            error=error,
        )

    finally:
        await api_client.close()


async def show_players_catalog(
    callback: CallbackQuery,
    source: str,
    requested_page: int,
) -> None:
    """
    Показывает кнопки участников или топа.
    """

    api_client, service = create_guild_service()

    try:
        _, combined_players = (
            await service.get_combined_players()
        )

        if source == "top":
            catalog = service.get_damage_catalog(
                combined_players
            )

            title = "💥 <b>Недельный топ урона</b>"
            description = (
                "Игроки бригады отсортированы "
                "по недельному урону."
            )
        else:
            catalog = service.get_members_catalog(
                combined_players
            )

            title = "👥 <b>Участники бригады</b>"
            description = (
                "Нажмите на игровой ник, "
                "чтобы открыть карточку участника."
            )

        (
            page_players,
            current_page,
            total_pages,
        ) = service.get_page(
            players=catalog,
            page=requested_page,
        )

        text = (
            f"{title}\n\n"
            f"{description}\n\n"
            f"Страница "
            f"<b>{current_page + 1}</b>"
            f" из "
            f"<b>{total_pages}</b>"
        )

        await edit_message(
            callback=callback,
            text=text,
            reply_markup=get_players_catalog_keyboard(
                players=page_players,
                current_page=current_page,
                total_pages=total_pages,
                source=source,
            ),
        )

    except Exception as error:
        await show_error(
            callback=callback,
            error=error,
        )

    finally:
        await api_client.close()


@router.callback_query(
    F.data.startswith("brigade:members:")
)
async def members_catalog_callback(
    callback: CallbackQuery,
) -> None:
    page_text = (
        callback.data or ""
    ).rsplit(":", maxsplit=1)[-1]

    try:
        page = int(page_text)
    except ValueError:
        page = 0

    await callback.answer(
        "Загружаю участников..."
    )

    await show_players_catalog(
        callback=callback,
        source="members",
        requested_page=page,
    )


@router.callback_query(
    F.data.startswith("brigade:top:")
)
async def damage_catalog_callback(
    callback: CallbackQuery,
) -> None:
    page_text = (
        callback.data or ""
    ).rsplit(":", maxsplit=1)[-1]

    try:
        page = int(page_text)
    except ValueError:
        page = 0

    await callback.answer(
        "Загружаю топ..."
    )

    await show_players_catalog(
        callback=callback,
        source="top",
        requested_page=page,
    )


@router.callback_query(
    F.data == "brigade:page:none"
)
async def page_number_callback(
    callback: CallbackQuery,
) -> None:
    await callback.answer()


@router.callback_query(
    F.data.startswith("brigade:player:")
)
async def player_card_callback(
    callback: CallbackQuery,
) -> None:
    """
    Открывает карточку игрока.

    Одновременно получает:
    - данные участника бригады;
    - недельный урон;
    - количество талантов.
    """

    parts = (
        callback.data or ""
    ).split(":")

    if len(parts) != 5:
        await callback.answer(
            "Неверные данные кнопки.",
            show_alert=True,
        )
        return

    try:
        user_id = int(parts[2])
        source = parts[3]
        page = int(parts[4])
    except ValueError:
        await callback.answer(
            "Не удалось определить игрока.",
            show_alert=True,
        )
        return

    if source not in {
        "members",
        "top",
    }:
        source = "members"

    await callback.answer(
        "Загружаю игрока..."
    )

    api_client, service = create_guild_service()

    try:
        _, combined_players = (
            await service.get_combined_players()
        )

        player = service.find_player(
            players=combined_players,
            user_id=user_id,
        )

        if player is None:
            raise RuntimeError(
                "Участник больше не найден в бригаде."
            )

        summary_payload = (
            await service.get_player_summary(
                user_id=user_id,
            )
        )

        talent_points_total = (
            service.extract_talent_points_total(
                summary_payload
            )
        )

        talents_text = (
            format_number(talent_points_total)
            if talent_points_total is not None
            else "нет данных"
        )

        weekly_rank = player.get(
            "weekly_rank"
        )

        weekly_rank_text = (
            str(weekly_rank)
            if weekly_rank is not None
            else "нет данных"
        )

        text = (
            f"👤 <b>"
            f"{html.escape(player['nickname'])}"
            f"</b>\n\n"
            f"🆔 <b>Игровой ID:</b>\n"
            f"<code>{player['user_id']}</code>\n\n"
            f"🎖 <b>Ранг в бригаде:</b>\n"
            f"{html.escape(player['guild_rank_name'])}\n\n"
            f"🏆 <b>Место в недельном топе:</b>\n"
            f"{html.escape(weekly_rank_text)}\n\n"
            f"💥 <b>Недельный урон:</b>\n"
            f"{format_number(player['weekly_damage'])}\n\n"
            f"🧬 <b>Таланты:</b>\n"
            f"{talents_text}"
        )

        await edit_message(
            callback=callback,
            text=text,
            reply_markup=get_player_card_keyboard(
                user_id=user_id,
                source=source,
                page=page,
            ),
        )

    except Exception as error:
        await show_error(
            callback=callback,
            error=error,
        )

    finally:
        await api_client.close()


@router.callback_query(
    F.data == "brigade:invite"
)
async def brigade_invite_callback(
    callback: CallbackQuery,
) -> None:
    await callback.answer()

    text = (
        "➕ <b>Пригласить в бригаду</b>\n\n"
        "Функцию подключим после проверки "
        "точного тела запроса "
        "<code>POST /api/guild/invite</code>."
    )

    await edit_message(
        callback=callback,
        text=text,
        reply_markup=get_brigade_back_keyboard(),
    )