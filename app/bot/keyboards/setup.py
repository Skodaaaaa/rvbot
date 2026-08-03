from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get_setup_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚔️ Сделать веткой рейдов",
                    callback_data="setup:topic:raids",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏕 Сделать веткой лагерей",
                    callback_data="setup:topic:camps",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Сделать веткой объявлений",
                    callback_data="setup:topic:announcements",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Показать настройки",
                    callback_data="setup:show",
                )
            ],
        ]
    )