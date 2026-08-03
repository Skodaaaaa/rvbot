from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.handlers.menu import edit_callback_message
from app.bot.keyboards.camp_menu import (
    get_camp_back_keyboard,
)


router = Router(name="camps")


@router.callback_query(F.data == "camps:status")
async def camp_status_callback(
    callback: CallbackQuery,
) -> None:
    text = (
        "🏕 <b>Состояние лагерей</b>\n\n"
        "Игровой API пока не подключён.\n\n"
        "В дальнейшем здесь будут отображаться:\n"
        "• состояние текущего лагеря;\n"
        "• время открытия;\n"
        "• время окончания;\n"
        "• текущий этап прохождения."
    )

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_camp_back_keyboard(),
    )


@router.callback_query(F.data == "camps:map")
async def camp_map_callback(
    callback: CallbackQuery,
) -> None:
    text = (
        "🗺 <b>Карта лагеря</b>\n\n"
        "Здесь будет показана информация из:\n"
        "<code>/api/dungeons/run/map</code>\n\n"
        "Сначала нам потребуется получить реальный пример "
        "JSON-ответа этого эндпоинта."
    )

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_camp_back_keyboard(),
    )


@router.callback_query(F.data == "camps:rating")
async def camp_rating_callback(
    callback: CallbackQuery,
) -> None:
    text = (
        "🏆 <b>Рейтинг лагеря</b>\n\n"
        "Здесь будут показаны данные рейтинга из:\n"
        "<code>/api/dungeons/run/ratings</code>"
    )

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_camp_back_keyboard(),
    )


@router.callback_query(F.data == "camps:damage")
async def camp_damage_callback(
    callback: CallbackQuery,
) -> None:
    text = (
        "💥 <b>Урон бригады</b>\n\n"
        "Здесь будет показан общий урон бригады "
        "по данным эндпоинта:\n"
        "<code>/api/dungeons/guild-damage</code>"
    )

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_camp_back_keyboard(),
    )


@router.callback_query(F.data == "camps:news")
async def camp_news_callback(
    callback: CallbackQuery,
) -> None:
    text = (
        "📜 <b>Новости лагерей</b>\n\n"
        "Здесь будут отображаться последние события "
        "из эндпоинта:\n"
        "<code>/api/dungeons/news</code>"
    )

    await edit_callback_message(
        callback=callback,
        text=text,
        reply_markup=get_camp_back_keyboard(),
    )