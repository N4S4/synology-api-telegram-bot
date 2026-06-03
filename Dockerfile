# v7 fix download + login
FROM python:3.11-slim

LABEL maintainer="N4S4"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY synology_api_telegram_bot/ ./synology_api_telegram_bot/

RUN mkdir -p /root/.config/synology-bot

CMD ["python", "-m", "synology_api_telegram_bot.main_bot"]
