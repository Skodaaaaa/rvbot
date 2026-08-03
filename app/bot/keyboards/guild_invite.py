from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get_invite_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопка отмены ввода игрового ID.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data="guild_invite:cancel",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад к бригаде",
                    callback_data="menu:brigade",
                )
            ],
        ]
    )


def get_invite_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Подтверждение отправки приглашения.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Отправить приглашение",
                    callback_data="guild_invite:confirm",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Ввести другой ID",
                    callback_data="guild_invite:change_id",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data="guild_invite:cancel",
                )
            ],
        ]
    )


def get_invite_result_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура после завершения операции.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Пригласить ещё",
                    callback_data="brigade:invite",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад к бригаде",
                    callback_data="menu:brigade",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="menu:main",
                )
            ],
        ]
    )