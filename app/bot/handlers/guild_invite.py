import html
import logging
from typing import Any

from aiogram import F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.guild_invite import (
    get_invite_cancel_keyboard,
    get_invite_confirmation_keyboard,
    get_invite_result_keyboard,
)
from app.bot.states.guild_invite import GuildInviteStates
from app.config import load_config
from app.game_api.client import GameApiClient
from app.game_api.endpoints import GameApiEndpoints
from app.game_api.exceptions import GameApiError
from app.storage.settings_storage import SettingsStorage


router = Router(name="guild_invite")

settings_storage = SettingsStorage()


INVITE_ERROR_MESSAGES: dict[str, str] = {
    "insufficient_role": (
        "Недостаточно игровых прав для приглашения "
        "в бригаду."
    ),
    "invalid_target": (
        "Этого игрока нельзя пригласить в бригаду."
    ),
    "target_already_in_guild": (
        "Игрок уже состоит в бригаде."
    ),
    "invite_already_sent": (
        "Этому игроку уже отправлено приглашение."
    ),
    "invite_limit_reached": (
        "Бригада достигла лимита исходящих приглашений."
    ),
    "target_invites_limit_reached": (
        "Игрок достиг лимита входящих приглашений."
    ),
}


def create_api_client() -> GameApiClient:
    """
    Создаёт игровой API-клиент владельца.
    """

    return GameApiClient(
        config=load_config(),
    )


async def user_is_allowed(
    callback: CallbackQuery,
) -> bool:
    """
    Приглашать игроков могут:

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

    chat = callback.message.chat

    if chat.type == "private":
        return False

    if await settings_storage.is_local_admin(
        chat_id=chat.id,
        telegram_user_id=user_id,
    ):
        return True

    try:
        member = await callback.bot.get_chat_member(
            chat_id=chat.id,
            user_id=user_id,
        )
    except Exception:
        return False

    return member.status in {
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.ADMINISTRATOR,
    }


def safe_int(
    value: Any,
) -> int | None:
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None

    if result <= 0:
        return None

    return result


def find_nested_value(
    payload: Any,
    target_keys: tuple[str, ...],
) -> Any:
    """
    Ищет первое подходящее поле
    во вложенном JSON.
    """

    if isinstance(payload, dict):
        for key in target_keys:
            if key in payload:
                value = payload[key]

                if value is not None:
                    return value

        for nested_value in payload.values():
            result = find_nested_value(
                payload=nested_value,
                target_keys=target_keys,
            )

            if result is not None:
                return result

    elif isinstance(payload, list):
        for nested_value in payload:
            result = find_nested_value(
                payload=nested_value,
                target_keys=target_keys,
            )

            if result is not None:
                return result

    return None


def extract_player_nickname(
    payload: Any,
) -> str | None:
    """
    Извлекает игровой ник из ответа профиля.

    Поддерживает разные названия полей,
    которые может использовать игровой API.
    """

    value = find_nested_value(
        payload=payload,
        target_keys=(
            "nickname",
            "nickName",
            "playerNickname",
            "player_nickname",
            "username",
            "userName",
            "displayName",
            "display_name",
            "nick",
        ),
    )

    if value is None:
        return None

    nickname = str(value).strip()

    return nickname or None

def extract_weekly_top_records(
    payload: Any,
) -> list[dict[str, Any]]:
    """
    Извлекает список игроков из ответа недельного топа.
    """

    if isinstance(payload, list):
        return [
            item
            for item in payload
            if isinstance(item, dict)
        ]

    if not isinstance(payload, dict):
        return []

    for field_name in (
        "items",
        "players",
        "top",
        "results",
        "records",
    ):
        candidate = payload.get(field_name)

        if isinstance(candidate, list):
            return [
                item
                for item in candidate
                if isinstance(item, dict)
            ]

    nested_data = payload.get("data")

    if isinstance(nested_data, list):
        return [
            item
            for item in nested_data
            if isinstance(item, dict)
        ]

    if isinstance(nested_data, dict):
        for field_name in (
            "items",
            "players",
            "top",
            "results",
            "records",
        ):
            candidate = nested_data.get(field_name)

            if isinstance(candidate, list):
                return [
                    item
                    for item in candidate
                    if isinstance(item, dict)
                ]

    return []


def find_nickname_in_weekly_top(
    payload: Any,
    user_id: int,
) -> str | None:
    """
    Ищет игровой ник в недельном топе по userId.
    """

    records = extract_weekly_top_records(
        payload
    )

    for record in records:
        record_user_id = safe_int(
            record.get("userId")
            or record.get("user_id")
            or record.get("id")
        )

        if record_user_id != user_id:
            continue

        nickname = (
            record.get("nickname")
            or record.get("nickName")
            or record.get("playerNickname")
            or record.get("username")
        )

        if nickname is None:
            return None

        nickname_text = str(
            nickname
        ).strip()

        return nickname_text or None

    return None

def extract_player_id(
    payload: Any,
) -> int | None:
    """
    Извлекает ID игрока из публичного профиля.
    """

    value = find_nested_value(
        payload=payload,
        target_keys=(
            "userId",
            "user_id",
            "playerId",
            "player_id",
        ),
    )

    return safe_int(value)


def extract_guild_id(
    guild_status: Any,
) -> int | None:
    """
    Извлекает guildId из /api/guild/status.
    """

    if not isinstance(guild_status, dict):
        return None

    guild = guild_status.get("guild")

    if isinstance(guild, dict):
        guild_id = safe_int(
            guild.get("guildId")
            or guild.get("id")
        )

        if guild_id is not None:
            return guild_id

    return safe_int(
        guild_status.get("guildId")
    )


def has_invite_privilege(
    guild_status: Any,
) -> bool:
    """
    Проверяет игровую привилегию inviteMember.
    """

    if not isinstance(guild_status, dict):
        return False

    privileges = guild_status.get(
        "myPrivileges",
        [],
    )

    if isinstance(privileges, list):
        return "inviteMember" in {
            str(privilege)
            for privilege in privileges
        }

    return False


def extract_invite_result(
    payload: Any,
) -> tuple[bool, str | None]:
    """
    Возвращает:

    - успешно ли отправлено приглашение;
    - код ошибки, если операция неуспешна.
    """

    if not isinstance(payload, dict):
        return False, None

    response_root = payload.get("data")

    if not isinstance(response_root, dict):
        response_root = payload

    success = response_root.get("success") is True

    error_code = response_root.get("error")

    if error_code is not None:
        error_code = str(error_code)

    return success, error_code


async def show_api_error(
    callback: CallbackQuery,
    error: Exception,
) -> None:
    """
    Показывает безопасную ошибку API.
    """

    if isinstance(error, GameApiError):
        status = (
            str(error.status)
            if error.status is not None
            else "неизвестен"
        )

        message = error.message

        logging.error(
            "Ошибка приглашения в бригаду. "
            "HTTP=%s, payload=%r",
            status,
            error.payload,
            exc_info=True,
        )
    else:
        status = "неизвестен"
        message = str(error)

        logging.exception(
            "Неожиданная ошибка приглашения "
            "в бригаду"
        )

    if callback.message is None:
        return

    await callback.message.edit_text(
        text=(
            "❌ <b>Не удалось отправить приглашение</b>\n\n"
            f"HTTP-статус: "
            f"<code>{html.escape(status)}</code>\n\n"
            f"Ошибка:\n"
            f"<code>{html.escape(message)}</code>"
        ),
        reply_markup=get_invite_result_keyboard(),
    )


@router.callback_query(
    F.data == "brigade:invite"
)
async def start_guild_invite(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Запускает ввод игрового ID.
    """

    if callback.message is None:
        return

    if not await user_is_allowed(callback):
        await callback.answer(
            "⛔ Приглашение доступно только "
            "администраторам.",
            show_alert=True,
        )
        return

    await state.clear()

    await state.set_state(
        GuildInviteStates.waiting_for_user_id
    )

    await callback.answer()

    await callback.message.edit_text(
        text=(
            "➕ <b>Приглашение в бригаду</b>\n\n"
            "Введите игровой ID игрока отдельным "
            "сообщением.\n\n"
            "Пример:\n"
            "<code>1179269112</code>"
        ),
        reply_markup=get_invite_cancel_keyboard(),
    )


@router.message(
    GuildInviteStates.waiting_for_user_id
)
async def receive_invited_user_id(
    message: Message,
    state: FSMContext,
) -> None:
    """
    Получает игровой ID и загружает
    публичный профиль игрока.
    """

    if message.from_user is None:
        return

    if not message.text:
        await message.answer(
            "❌ Отправьте игровой ID обычным текстом.",
            reply_markup=get_invite_cancel_keyboard(),
        )
        return

    user_id_text = (
        message.text
        .strip()
        .replace(" ", "")
    )

    target_user_id = safe_int(
        user_id_text
    )

    if target_user_id is None:
        await message.answer(
            "❌ Некорректный игровой ID.\n\n"
            "ID должен состоять только из цифр.\n\n"
            "Пример:\n"
            "<code>1179269112</code>",
            reply_markup=get_invite_cancel_keyboard(),
        )
        return

    status_message = await message.answer(
        "🔎 <b>Ищу игрока...</b>"
    )

    api_client = create_api_client()

    try:
        summary_payload = (
            await api_client.get_player_summary(
                user_id=target_user_id,
            )
        )

        nickname = extract_player_nickname(
            summary_payload
        )

        profile_user_id = extract_player_id(
            summary_payload
        )

        if (
            profile_user_id is not None
            and profile_user_id != target_user_id
        ):
            raise RuntimeError(
                "Игровой API вернул профиль "
                "другого пользователя."
            )

        # Если в summary нет ника,
        # пробуем найти игрока в недельном топе.
        if nickname is None:
            try:
                weekly_top_payload = (
                    await api_client.get_weekly_top(
                        limit=3000,
                    )
                )

                nickname = find_nickname_in_weekly_top(
                    payload=weekly_top_payload,
                    user_id=target_user_id,
                )

            except Exception:
                logging.exception(
                    "Не удалось найти ник игрока "
                    "в недельном топе"
                )

        # Последний резервный вариант:
        # показываем понятную подпись с игровым ID.
        if nickname is None:
            nickname = f"Игрок {target_user_id}"

        await state.update_data(
            target_user_id=target_user_id,
            target_nickname=nickname,
        )

        await state.set_state(
            GuildInviteStates.waiting_for_confirmation
        )

        await status_message.edit_text(
            text=(
                "➕ <b>Подтверждение приглашения</b>\n\n"
                f"👤 <b>Игрок:</b>\n"
                f"{html.escape(nickname)}\n\n"
                f"🆔 <b>Игровой ID:</b>\n"
                f"<code>{target_user_id}</code>\n\n"
                "Отправить приглашение в бригаду?"
            ),
            reply_markup=(
                get_invite_confirmation_keyboard()
            ),
        )

    except GameApiError as error:
        logging.error(
            "Не удалось получить профиль "
            "приглашаемого игрока. HTTP=%s, payload=%r",
            error.status,
            error.payload,
            exc_info=True,
        )

        await status_message.edit_text(
            text=(
                "❌ <b>Игрок не найден</b>\n\n"
                f"Не удалось получить профиль игрока "
                f"с ID:\n"
                f"<code>{target_user_id}</code>\n\n"
                f"Ошибка:\n"
                f"<code>"
                f"{html.escape(error.message)}"
                f"</code>"
            ),
            reply_markup=get_invite_cancel_keyboard(),
        )

    except Exception as error:
        logging.exception(
            "Ошибка проверки приглашаемого игрока"
        )

        await status_message.edit_text(
            text=(
                "❌ <b>Не удалось проверить игрока</b>\n\n"
                f"<code>{html.escape(str(error))}</code>"
            ),
            reply_markup=get_invite_cancel_keyboard(),
        )

    finally:
        await api_client.close()


@router.callback_query(
    GuildInviteStates.waiting_for_confirmation,
    F.data == "guild_invite:confirm",
)
async def confirm_guild_invite(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Отправляет игровое приглашение.
    """

    if callback.message is None:
        return

    if not await user_is_allowed(callback):
        await callback.answer(
            "⛔ Недостаточно прав.",
            show_alert=True,
        )
        return

    state_data = await state.get_data()

    target_user_id = safe_int(
        state_data.get("target_user_id")
    )

    target_nickname = str(
        state_data.get("target_nickname")
        or "Игрок"
    )

    if target_user_id is None:
        await callback.answer(
            "Данные приглашения потеряны. "
            "Начните заново.",
            show_alert=True,
        )

        await state.clear()
        return

    await callback.answer(
        "Отправляю приглашение..."
    )

    api_client = create_api_client()

    try:
        guild_status = (
            await api_client.get_guild_status()
        )

        guild_id = extract_guild_id(
            guild_status
        )

        if guild_id is None:
            raise RuntimeError(
                "Не удалось определить guildId "
                "текущей бригады."
            )

        if not has_invite_privilege(
            guild_status
        ):
            raise RuntimeError(
                "Игровой аккаунт не имеет привилегии "
                "inviteMember."
            )

        members = guild_status.get(
            "members",
            [],
        )

        if isinstance(members, list):
            for member in members:
                if not isinstance(member, dict):
                    continue

                member_user_id = safe_int(
                    member.get("userId")
                )

                if member_user_id == target_user_id:
                    await state.clear()

                    await callback.message.edit_text(
                        text=(
                            "ℹ️ <b>Игрок уже в бригаде</b>\n\n"
                            f"👤 {html.escape(target_nickname)}\n"
                            f"🆔 <code>{target_user_id}</code>"
                        ),
                        reply_markup=get_invite_result_keyboard(),
                    )
                    return

        response_payload = await api_client.request(
            method="POST",
            path=GameApiEndpoints.GUILD_INVITE,
            json_body={
                "guildId": guild_id,
                "userId": target_user_id,
            },
        )

        success, error_code = extract_invite_result(
            response_payload
        )

        if not success:
            error_message = INVITE_ERROR_MESSAGES.get(
                error_code or "",
                (
                    "Игровой сервер не подтвердил "
                    "отправку приглашения."
                    if error_code is None
                    else (
                        "Игровой сервер вернул ошибку: "
                        f"{error_code}"
                    )
                ),
            )

            await callback.message.edit_text(
                text=(
                    "❌ <b>Приглашение не отправлено</b>\n\n"
                    f"👤 {html.escape(target_nickname)}\n"
                    f"🆔 <code>{target_user_id}</code>\n\n"
                    f"{html.escape(error_message)}"
                ),
                reply_markup=get_invite_result_keyboard(),
            )

            await state.clear()
            return

        await state.clear()

        await callback.message.edit_text(
            text=(
                "✅ <b>Приглашение отправлено</b>\n\n"
                f"👤 <b>Игрок:</b>\n"
                f"{html.escape(target_nickname)}\n\n"
                f"🆔 <b>Игровой ID:</b>\n"
                f"<code>{target_user_id}</code>"
            ),
            reply_markup=get_invite_result_keyboard(),
        )

    except Exception as error:
        await state.clear()

        await show_api_error(
            callback=callback,
            error=error,
        )

    finally:
        await api_client.close()


@router.callback_query(
    GuildInviteStates.waiting_for_confirmation,
    F.data == "guild_invite:change_id",
)
async def change_invited_user_id(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Возвращает администратора к вводу ID.
    """

    if callback.message is None:
        return

    await state.set_state(
        GuildInviteStates.waiting_for_user_id
    )

    await callback.answer()

    await callback.message.edit_text(
        text=(
            "✏️ <b>Введите другой игровой ID</b>\n\n"
            "Пример:\n"
            "<code>1179269112</code>"
        ),
        reply_markup=get_invite_cancel_keyboard(),
    )


@router.callback_query(
    F.data == "guild_invite:cancel"
)
async def cancel_guild_invite(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Отменяет приглашение на любом этапе.
    """

    await state.clear()

    await callback.answer(
        "Приглашение отменено."
    )

    if callback.message is not None:
        await callback.message.edit_text(
            text="❌ Приглашение отменено.",
            reply_markup=get_invite_result_keyboard(),
        )