from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Открыть рейд",
                    callback_data="admin:raid:create",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏁 Завершить рейд",
                    callback_data="admin:raid:finish",
                ),
                InlineKeyboardButton(
                    text="❌ Отменить рейд",
                    callback_data="admin:raid:cancel",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔗 Настройка веток",
                    callback_data="admin:setup",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Главное меню",
                    callback_data="menu:main",
                )
            ],
        ]
    )


def get_admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Назад в админ-панель",
                    callback_data="menu:admin",
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
