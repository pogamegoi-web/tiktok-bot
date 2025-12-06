FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install python-telegram-bot requests
WORKDIR /app
COPY bot.py .
CMD ["python", "bot.py"]


