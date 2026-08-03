from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards.main_menu import get_main_menu_keyboard


router = Router(name="start")


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    """
    Обрабатывает команду /start.
    """

    user_name = "пользователь"

    if message.from_user is not None:
        user_name = message.from_user.full_name

    text = (
        f"Привет, {user_name}!\n\n"
        "Я бот для управления событиями бригады Роза Ветров.\n\n"
        "Через меня можно будет:\n"
        "• смотреть информацию о бригаде;\n"
        "• создавать и отслеживать рейды;\n"
        "• получать уведомления о лагерях;\n"
        "• управлять событиями через админ-панель.\n\n"
        "Нажми нужную кнопку:"
    )

    await message.answer(
        text=text,
        reply_markup=get_main_menu_keyboard(),
    )