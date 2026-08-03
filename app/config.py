from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Config:
    """
    Все настройки приложения.
    """

    bot_token: str
    owner_telegram_id: int

    game_api_base_url: str
    game_access_token: str
    game_refresh_token: str

    game_language: str
    game_country: str
    game_platform: str


def load_config() -> Config:
    """
    Загружает настройки из файла .env.
    """

    load_dotenv()

    bot_token = getenv("BOT_TOKEN", "").strip()
    owner_telegram_id_raw = getenv(
        "OWNER_TELEGRAM_ID",
        "0",
    ).strip()

    game_api_base_url = getenv(
        "GAME_API_BASE_URL",
        "https://prison.luckygem.online",
    ).strip().rstrip("/")

    game_access_token = getenv(
        "GAME_ACCESS_TOKEN",
        "",
    ).strip()

    game_refresh_token = getenv(
        "GAME_REFRESH_TOKEN",
        "",
    ).strip()

    game_language = getenv(
        "GAME_LANGUAGE",
        "ru",
    ).strip()

    game_country = getenv(
        "GAME_COUNTRY",
        "RU",
    ).strip()

    game_platform = getenv(
        "GAME_PLATFORM",
        "web",
    ).strip()

    if not bot_token:
        raise RuntimeError(
            "Не найден BOT_TOKEN. Проверь файл .env."
        )

    try:
        owner_telegram_id = int(owner_telegram_id_raw)
    except ValueError as error:
        raise RuntimeError(
            "OWNER_TELEGRAM_ID должен быть целым числом."
        ) from error

    return Config(
        bot_token=bot_token,
        owner_telegram_id=owner_telegram_id,
        game_api_base_url=game_api_base_url,
        game_access_token=game_access_token,
        game_refresh_token=game_refresh_token,
        game_language=game_language,
        game_country=game_country,
        game_platform=game_platform,
    )