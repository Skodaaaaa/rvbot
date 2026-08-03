from aiogram import F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import CallbackQuery

from app.bot.handlers.menu import edit_callback_message
from app.bot.keyboards.admin_menu import (
    get_admin_back_keyboard,
)
from app.bot.keyboards.setup import (
    get_setup_keyboard,
)
from app.config import load_config
from app.storage.settings_storage import SettingsStorage


router = Router(name="admin")

settings_storage = SettingsStorage()


async def user_is_admin(
    callback: CallbackQuery,
) -> bool:
    """
    Проверяет права пользователя.

    Доступ разрешается:
    1. Владельцу из OWNER_TELEGRAM_ID.
    2. Администратору Telegram-группы.
    3. Локальному администратору из settings.json.
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


async def deny_if_not_admin(
    callback: CallbackQuery,
) -> bool:
    """
    Возвращает True, если доступ запрещён.
    """

    if await user_is_admin(callback):
        return False

    await callback.answer(
        text="⛔ Недостаточно прав.",
        show_alert=True,
    )

    return True


@router.callback_query(F.data == "admin:raid:create")
async def create_raid_callback(
    callback: CallbackQuery,
) -> None:
    if await deny_if_not_admin(callback):
        return

    text = (
        "➕ <b>Объявление рейда</b>\n\n"
        "На следующем этапе здесь запустится "
        "пошаговый диалог создания рейда:\n\n"
        "1. Название рейда.\n"
        "2. Описание.\n"
        "3. Дата начала.\n"
        "4. Время начала.\n"
        "5. Время окончания.\n"
        "6. Подтверждение."
    )

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_admin_back_keyboard(),
    )


@router.callback_query(F.data == "admin:raid:edit")
async def edit_raid_callback(
    callback: CallbackQuery,
) -> None:
    if await deny_if_not_admin(callback):
        return

    text = (
        "✏️ <b>Изменение рейда</b>\n\n"
        "Активный рейд пока отсутствует."
    )

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_admin_back_keyboard(),
    )


@router.callback_query(F.data == "admin:raid:finish")
async def finish_raid_callback(
    callback: CallbackQuery,
) -> None:
    if await deny_if_not_admin(callback):
        return

    text = (
        "🏁 <b>Завершение рейда</b>\n\n"
        "Активный рейд пока отсутствует."
    )

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_admin_back_keyboard(),
    )


@router.callback_query(F.data == "admin:raid:cancel")
async def cancel_raid_callback(
    callback: CallbackQuery,
) -> None:
    if await deny_if_not_admin(callback):
        return

    text = (
        "❌ <b>Отмена рейда</b>\n\n"
        "Запланированный рейд пока отсутствует."
    )

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_admin_back_keyboard(),
    )


@router.callback_query(F.data == "admin:setup")
async def admin_setup_callback(
    callback: CallbackQuery,
) -> None:
    if await deny_if_not_admin(callback):
        return

    if callback.message is None:
        return

    text = (
        "🔗 <b>Настройка веток</b>\n\n"
        "Привязка выполняется к той ветке, "
        "в которой находится это сообщение.\n\n"
        "Для более надёжной настройки рекомендуется "
        "открыть нужную тему и вызвать там команду "
        "<code>/setup</code>."
    )

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_setup_keyboard(),
    )


@router.callback_query(F.data == "admin:api")
async def api_test_callback(
    callback: CallbackQuery,
) -> None:
    if await deny_if_not_admin(callback):
        return

    text = (
        "🧪 <b>Проверка игрового API</b>\n\n"
        "Игровой клиент пока не подключён.\n\n"
        "После создания локальной системы рейдов "
        "мы добавим сюда безопасные тесты:\n"
        "• проверка токена;\n"
        "• получение игрока;\n"
        "• получение бригады;\n"
        "• получение состояния лагерей."
    )

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_admin_back_keyboard(),
    )