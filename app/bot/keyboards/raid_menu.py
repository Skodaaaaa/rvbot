from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get_raid_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Меню раздела «Рейды».
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚔️ Текущий рейд",
                    callback_data="raids:current",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👥 Участники рейда",
                    callback_data="raids:participants",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📜 История рейдов",
                    callback_data="raids:history",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Главное меню",
                    callback_data="menu:main",
                ),
            ],
        ]
    )


def get_raid_back_keyboard() -> InlineKeyboardMarkup:
    """
    Возврат в меню рейдов.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Назад к рейдам",
                    callback_data="menu:raids",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="menu:main",
                ),
            ],
        ]
    )