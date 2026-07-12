FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ bot/
COPY database/ database/
COPY scripts/ scripts/
COPY config.py .

ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/app/data/bot_database.db

CMD ["python", "-m", "bot.main"]
