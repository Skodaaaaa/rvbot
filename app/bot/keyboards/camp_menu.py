from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get_camp_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Меню раздела «Лагеря».
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏕 Состояние лагерей",
                    callback_data="camps:status",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗺 Карта лагеря",
                    callback_data="camps:map",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Рейтинг",
                    callback_data="camps:rating",
                ),
                InlineKeyboardButton(
                    text="💥 Урон бригады",
                    callback_data="camps:damage",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📜 Новости",
                    callback_data="camps:news",
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


def get_camp_back_keyboard() -> InlineKeyboardMarkup:
    """
    Возврат в меню лагерей.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Назад к лагерям",
                    callback_data="menu:camps",
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