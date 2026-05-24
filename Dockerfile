FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY synology_api_telegram_bot/ ./synology_api_telegram_bot/
COPY setup.py README.md ./

# Create config directory
RUN mkdir -p /root/.config/synology-bot

# Run the bot
CMD ["python", "-m", "synology_api_telegram_bot.main_bot"]
