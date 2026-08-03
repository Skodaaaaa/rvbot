from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class TopicSettings:
    raids: int | None = None
    camps: int | None = None
    announcements: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "TopicSettings":
        data = data or {}

        return cls(
            raids=data.get("raids"),
            camps=data.get("camps"),
            announcements=data.get("announcements"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ChatSettings:
    chat_id: int
    title: str | None = None
    timezone: str = "Europe/Moscow"
    topics: TopicSettings = field(default_factory=TopicSettings)
    admins: list[int] = field(default_factory=list)

    @classmethod
    def from_dict(
        cls,
        chat_id: int,
        data: dict[str, Any],
    ) -> "ChatSettings":
        raw_admins = data.get("admins", [])

        admins: list[int] = []

        for admin_id in raw_admins:
            try:
                admins.append(int(admin_id))
            except (TypeError, ValueError):
                continue

        return cls(
            chat_id=chat_id,
            title=data.get("title"),
            timezone=data.get("timezone", "Europe/Moscow"),
            topics=TopicSettings.from_dict(data.get("topics")),
            admins=admins,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "timezone": self.timezone,
            "topics": self.topics.to_dict(),
            "admins": self.admins,
        }