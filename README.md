# Prison Brigade Bot v2

Чистая версия Telegram-бота для бригады игры «Тюряга».

## Запуск на Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m app.main
```

Перед запуском заполните `.env`.

## Уже работает

- `/start`, `/menu`, `/id`, `/setup`;
- настройка веток Telegram;
- информация о бригаде;
- кнопочный список участников;
- недельный топ урона;
- карточка игрока с талантами;
- автоматическая попытка обновить токен при `401` и `403 Unauthorized`.
