from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get_brigade_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Главное меню раздела «Бригада».
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Информация о бригаде",
                    callback_data="brigade:info",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Участники",
                    callback_data="brigade:members:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💥 Топ урона",
                    callback_data="brigade:top:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ Пригласить в бригаду",
                    callback_data="brigade:invite",
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


def get_brigade_back_keyboard() -> InlineKeyboardMarkup:
    """
    Возврат в раздел бригады.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
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


def shorten_button_text(
    value: str,
    max_length: int = 34,
) -> str:
    """
    Сокращает слишком длинный ник.
    """

    if len(value) <= max_length:
        return value

    return value[: max_length - 1] + "…"


def format_short_damage(
    damage: int,
) -> str:
    """
    Краткая запись урона для кнопок.
    """

    if damage >= 1_000_000_000:
        value = damage / 1_000_000_000
        return f"{value:.2f}ккк".replace(".", ",")

    if damage >= 1_000_000:
        value = damage / 1_000_000
        return f"{value:.1f}кк".replace(".", ",")

    if damage >= 1_000:
        value = damage / 1_000
        return f"{value:.1f}к".replace(".", ",")

    return str(damage)


def get_players_catalog_keyboard(
    players: list[dict],
    current_page: int,
    total_pages: int,
    source: str,
) -> InlineKeyboardMarkup:
    """
    Создаёт кнопочный список участников или топа.

    source:
    - members
    - top
    """

    rows: list[list[InlineKeyboardButton]] = []

    for index, player in enumerate(players):
        nickname = shorten_button_text(
            player["nickname"]
        )

        if source == "top":
            global_position = (
                current_page * 8
                + index
                + 1
            )

            if global_position == 1:
                prefix = "🥇"
            elif global_position == 2:
                prefix = "🥈"
            elif global_position == 3:
                prefix = "🥉"
            else:
                prefix = f"{global_position}."

            damage = format_short_damage(
                player["weekly_damage"]
            )

            button_text = (
                f"{prefix} {nickname} — {damage}"
            )
        else:
            button_text = nickname

        rows.append(
            [
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=(
                        f"brigade:player:"
                        f"{player['user_id']}:"
                        f"{source}:"
                        f"{current_page}"
                    ),
                )
            ]
        )

    navigation: list[InlineKeyboardButton] = []

    if current_page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=(
                    f"brigade:{source}:"
                    f"{current_page - 1}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            text=(
                f"{current_page + 1}"
                f" / "
                f"{total_pages}"
            ),
            callback_data="brigade:page:none",
        )
    )

    if current_page < total_pages - 1:
        navigation.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=(
                    f"brigade:{source}:"
                    f"{current_page + 1}"
                ),
            )
        )

    rows.append(navigation)

    rows.append(
        [
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=(
                    f"brigade:{source}:"
                    f"{current_page}"
                ),
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                text="◀️ Назад к бригаде",
                callback_data="menu:brigade",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )


def get_player_card_keyboard(
    user_id: int,
    source: str,
    page: int,
) -> InlineKeyboardMarkup:
    """
    Кнопки карточки игрока.
    """

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Обновить данные",
                    callback_data=(
                        f"brigade:player:"
                        f"{user_id}:"
                        f"{source}:"
                        f"{page}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад к списку",
                    callback_data=(
                        f"brigade:{source}:{page}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Раздел бригады",
                    callback_data="menu:brigade",
                )
            ],
        ]
    )