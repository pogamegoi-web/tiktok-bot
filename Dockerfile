FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pyTelegramBotAPI yt-dlp requests

COPY . .

CMD ["python", "bot.py"]

