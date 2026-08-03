from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Главное меню Telegram-бота.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Бригада",
                    callback_data="menu:brigade",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⚔️ Рейды",
                    callback_data="menu:raids",
                ),
                InlineKeyboardButton(
                    text="🏕 Лагеря",
                    callback_data="menu:camps",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🛠 Админ-панель",
                    callback_data="menu:admin",
                ),
            ],
        ]
    )