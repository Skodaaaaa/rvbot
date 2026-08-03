from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.admin_menu import (
    get_admin_menu_keyboard,
)
from app.bot.keyboards.brigade_menu import (
    get_brigade_menu_keyboard,
)
from app.bot.keyboards.camp_menu import (
    get_camp_menu_keyboard,
)
from app.bot.keyboards.main_menu import (
    get_main_menu_keyboard,
)
from app.bot.keyboards.raid_menu import (
    get_raid_menu_keyboard,
)


router = Router(name="menu")


MAIN_MENU_TEXT = (
    "🏠 <b>Главное меню</b>\n\n"
    "Выбери нужный раздел:"
)

BRIGADE_MENU_TEXT = (
    "👥 <b>Бригада</b>\n\n"
    "Здесь можно посмотреть информацию о бригаде, "
    "её участниках и журнале событий."
)

RAID_MENU_TEXT = (
    "⚔️ <b>Рейды</b>\n\n"
    "Здесь отображаются текущий рейд, "
    "его участники и история прошедших рейдов."
)

CAMP_MENU_TEXT = (
    "🏕 <b>Лагеря</b>\n\n"
    "Здесь будет отображаться состояние лагерей, "
    "карта, рейтинг и урон бригады."
)

ADMIN_MENU_TEXT = (
    "🛠 <b>Админ-панель</b>\n\n"
    "Управление рейдами, ветками и игровым API."
)


async def edit_callback_message(
    callback: CallbackQuery,
    text: str,
    reply_markup,
) -> None:
    """
    Редактирует сообщение с меню.

    Telegram может вернуть ошибку, если пользователь
    нажал ту же кнопку повторно и содержимое не изменилось.
    Такую ошибку безопасно игнорируем.
    """

    await callback.answer()

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


@router.message(Command("menu"))
async def menu_command(message: Message) -> None:
    """
    Показывает главное меню по команде /menu.
    """

    await message.answer(
        text=MAIN_MENU_TEXT,
        reply_markup=get_main_menu_keyboard(),
    )


@router.callback_query(F.data == "menu:main")
async def main_menu_callback(
    callback: CallbackQuery,
) -> None:
    await edit_callback_message(
        callback=callback,
        text=MAIN_MENU_TEXT,
        reply_markup=get_main_menu_keyboard(),
    )


@router.callback_query(F.data == "menu:brigade")
async def brigade_menu_callback(
    callback: CallbackQuery,
) -> None:
    await edit_callback_message(
        callback=callback,
        text=BRIGADE_MENU_TEXT,
        reply_markup=get_brigade_menu_keyboard(),
    )


@router.callback_query(F.data == "menu:raids")
async def raid_menu_callback(
    callback: CallbackQuery,
) -> None:
    await edit_callback_message(
        callback=callback,
        text=RAID_MENU_TEXT,
        reply_markup=get_raid_menu_keyboard(),
    )


@router.callback_query(F.data == "menu:camps")
async def camp_menu_callback(
    callback: CallbackQuery,
) -> None:
    await edit_callback_message(
        callback=callback,
        text=CAMP_MENU_TEXT,
        reply_markup=get_camp_menu_keyboard(),
    )


@router.callback_query(F.data == "menu:admin")
async def admin_menu_callback(
    callback: CallbackQuery,
) -> None:
    await edit_callback_message(
        callback=callback,
        text=ADMIN_MENU_TEXT,
        reply_markup=get_admin_menu_keyboard(),
    )