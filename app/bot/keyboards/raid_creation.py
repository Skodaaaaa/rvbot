from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_raid_creation_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отменить создание",
                    callback_data="raid:create:cancel",
                )
            ]
        ]
    )


def get_raid_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Опубликовать",
                    callback_data="raid:create:confirm",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data="raid:create:cancel",
                )
            ],
        ]
    )
