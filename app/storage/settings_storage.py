from pathlib import Path
from typing import Literal

from app.models.settings import ChatSettings
from app.storage.json_storage import JsonStorage


TopicType = Literal[
    "raids",
    "camps",
    "announcements",
]


class SettingsStorage:
    """
    Хранит настройки Telegram-чатов и веток.
    """

    def __init__(
        self,
        file_path: str | Path = "data/settings.json",
    ) -> None:
        self.storage = JsonStorage(
            file_path=file_path,
            default_data={
                "chats": {},
            },
        )

    async def initialize(self) -> None:
        await self.storage.initialize()

    async def get_chat(
        self,
        chat_id: int,
    ) -> ChatSettings | None:
        data = await self.storage.read()

        chats = data.get("chats", {})
        raw_chat = chats.get(str(chat_id))

        if not isinstance(raw_chat, dict):
            return None

        return ChatSettings.from_dict(
            chat_id=chat_id,
            data=raw_chat,
        )

    async def get_or_create_chat(
        self,
        chat_id: int,
        title: str | None = None,
    ) -> ChatSettings:
        data = await self.storage.read()

        chats = data.setdefault(
            "chats",
            {},
        )

        chat_key = str(chat_id)
        raw_chat = chats.get(chat_key)

        if isinstance(raw_chat, dict):
            chat_settings = ChatSettings.from_dict(
                chat_id=chat_id,
                data=raw_chat,
            )

            if title and chat_settings.title != title:
                chat_settings.title = title
                chats[chat_key] = chat_settings.to_dict()
                await self.storage.write(data)

            return chat_settings

        chat_settings = ChatSettings(
            chat_id=chat_id,
            title=title,
        )

        chats[chat_key] = chat_settings.to_dict()

        await self.storage.write(data)

        return chat_settings

    async def set_topic(
        self,
        chat_id: int,
        topic_type: TopicType,
        thread_id: int,
        title: str | None = None,
    ) -> ChatSettings:
        data = await self.storage.read()

        chats = data.setdefault(
            "chats",
            {},
        )

        chat_key = str(chat_id)
        raw_chat = chats.get(chat_key, {})

        if not isinstance(raw_chat, dict):
            raw_chat = {}

        chat_settings = ChatSettings.from_dict(
            chat_id=chat_id,
            data=raw_chat,
        )

        if title:
            chat_settings.title = title

        setattr(
            chat_settings.topics,
            topic_type,
            thread_id,
        )

        chats[chat_key] = chat_settings.to_dict()

        await self.storage.write(data)

        return chat_settings

    async def remove_topic(
        self,
        chat_id: int,
        topic_type: TopicType,
    ) -> ChatSettings:
        data = await self.storage.read()

        chats = data.setdefault(
            "chats",
            {},
        )

        chat_key = str(chat_id)
        raw_chat = chats.get(chat_key, {})

        if not isinstance(raw_chat, dict):
            raw_chat = {}

        chat_settings = ChatSettings.from_dict(
            chat_id=chat_id,
            data=raw_chat,
        )

        setattr(
            chat_settings.topics,
            topic_type,
            None,
        )

        chats[chat_key] = chat_settings.to_dict()

        await self.storage.write(data)

        return chat_settings

    async def add_admin(
        self,
        chat_id: int,
        telegram_user_id: int,
    ) -> ChatSettings:
        data = await self.storage.read()

        chats = data.setdefault(
            "chats",
            {},
        )

        chat_key = str(chat_id)
        raw_chat = chats.get(chat_key, {})

        if not isinstance(raw_chat, dict):
            raw_chat = {}

        chat_settings = ChatSettings.from_dict(
            chat_id=chat_id,
            data=raw_chat,
        )

        if telegram_user_id not in chat_settings.admins:
            chat_settings.admins.append(
                telegram_user_id
            )

        chats[chat_key] = chat_settings.to_dict()

        await self.storage.write(data)

        return chat_settings

    async def is_local_admin(
        self,
        chat_id: int,
        telegram_user_id: int,
    ) -> bool:
        chat_settings = await self.get_chat(
            chat_id=chat_id,
        )

        if chat_settings is None:
            return False

        return telegram_user_id in chat_settings.admins