# My English Teacher Bot 🇬🇧

Телеграм-бот для разговорной практики английского языка с AI.
Помогает преодолеть страх говорить, объясняет грамматику и расширяет словарный запас в удобном стиле общения.

## Возможности

- 🗣 Разговорная практика без стеснения
- 📚 Карточки слов с AI-генерацией и повторением
- 📖 Грамматика: объяснения + упражнения
- 🔔 Напоминания о занятиях по местному времени
- 📊 Прогресс и серия дней (`/progress`)
- 💬 Обратная связь (`/feedback`)

## Технологии

- Python 3.10+
- python-telegram-bot
- OpenRouter (AI)
- SQLite (WAL mode)
- APScheduler (напоминания)

## Запуск локально

1. Клонировать репозиторий
2. Создать venv и установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Скопировать `.env.example` → `.env` и заполнить ключи
4. Запустить:
   ```bash
   python -m bot.main
   ```

## Деплой (Docker)

1. Скопировать `.env` на сервер (не коммитить в git)
2. Собрать и запустить:
   ```bash
   docker compose up -d --build
   ```
3. База хранится в Docker volume `bot-data` (`/app/data/bot_database.db`)

Просмотр логов:
```bash
docker compose logs -f bot
```

Остановка:
```bash
docker compose down
```

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен от @BotFather |
| `OPENROUTER_API_KEY` | Ключ OpenRouter |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` |
| `MODEL_DIALOG` | Модель для диалога |
| `DAILY_COST_LIMIT_USD` | Дневной потолок расходов на AI |
| `ADMIN_USER_ID` | Telegram ID admin (алерты, `/stats`) |
| `PROXY_URL` | Опционально: HTTP/SOCKS5 прокси |
| `DB_PATH` | Путь к SQLite (по умолчанию `./bot_database.db`) |

## Бэкап базы данных

**Linux / macOS:**
```bash
chmod +x scripts/backup_db.sh
DB_PATH=./bot_database.db ./scripts/backup_db.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\backup_db.ps1
```

**В Docker:**
```bash
docker compose exec bot sh scripts/backup_db.sh
```

Рекомендуется cron раз в сутки:
```cron
0 3 * * * docker compose -f /path/to/docker-compose.yml exec -T bot sh scripts/backup_db.sh
```

Копии сохраняются в `./backups/`, хранятся последние 14.

## Admin-команды

| Команда | Кто | Описание |
|---------|-----|----------|
| `/stats` | `ADMIN_USER_ID` | DAU, воронка, расход AI, отзывы |

## Чеклист перед бета-запуском

- [ ] Бот отвечает после рестарта (история и сессии в SQLite)
- [ ] `ADMIN_USER_ID` задан, `/stats` работает
- [ ] `DAILY_COST_LIMIT_USD` настроен под бюджет
- [ ] Напоминания проверены в prod timezone
- [ ] Настроен ежедневный бэкап БД
- [ ] Токен бота не публиковался в открытом доступе

## Статус

✅ MVP готов к бета-тесту (10–30 пользователей). Монетизация (ЮKassa) — следующий этап.
