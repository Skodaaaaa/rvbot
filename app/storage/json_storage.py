import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


class JsonStorage:
    """
    Универсальное безопасное хранилище JSON.

    Перед записью:
    1. Создаёт резервную копию старого файла.
    2. Записывает данные во временный файл.
    3. Проверяет временный JSON.
    4. Заменяет основной файл.
    """

    def __init__(
        self,
        file_path: str | Path,
        default_data: dict[str, Any] | None = None,
    ) -> None:
        self.file_path = Path(file_path)
        self.default_data = default_data or {}
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._initialize_sync)

    def _initialize_sync(self) -> None:
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.file_path.exists():
            self._write_sync(self.default_data)

    async def read(self) -> dict[str, Any]:
        async with self._lock:
            return await asyncio.to_thread(self._read_sync)

    def _read_sync(self) -> dict[str, Any]:
        self._initialize_sync()

        try:
            with self.file_path.open(
                mode="r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Файл {self.file_path} содержит повреждённый JSON."
            ) from error

        if not isinstance(data, dict):
            raise RuntimeError(
                f"В файле {self.file_path} должен находиться JSON-объект."
            )

        return data

    async def write(self, data: dict[str, Any]) -> None:
        async with self._lock:
            await asyncio.to_thread(
                self._write_sync,
                data,
            )

    def _write_sync(self, data: dict[str, Any]) -> None:
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_file = self.file_path.with_suffix(
            self.file_path.suffix + ".tmp"
        )

        if self.file_path.exists():
            self._create_backup_sync()

        with temp_file.open(
            mode="w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        with temp_file.open(
            mode="r",
            encoding="utf-8",
        ) as file:
            json.load(file)

        temp_file.replace(self.file_path)

    def _create_backup_sync(self) -> None:
        backup_directory = (
            self.file_path.parent / "backups"
        )

        backup_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S-%f"
        )

        backup_file = backup_directory / (
            f"{self.file_path.stem}_{timestamp}"
            f"{self.file_path.suffix}"
        )

        shutil.copy2(
            self.file_path,
            backup_file,
        )