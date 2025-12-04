import telebot
import subprocess
import os
import re
from config import BOT_TOKEN, ADMIN_ID

bot = telebot.TeleBot(BOT_TOKEN)

def download_video(url):
    output = f"video_{os.getpid()}.mp4"
    cmd = ["yt-dlp", "-f", "best[ext=mp4]/best", "-o", output, "--no-playlist", url]
    try:
        subprocess.run(cmd, check=True, timeout=120)
        if os.path.exists(output):
            return output
    except:
        pass
    return None

@bot.message_handler(func=lambda m: True)
def handle(message):
    text = message.text or ""
    urls = re.findall(r'https?://[^\s]+', text)
    for url in urls:
        if any(x in url for x in ['tiktok.com', 'instagram.com', 'youtube.com']):
            bot.reply_to(message, "⏳ Скачиваю...")
            video = download_video(url)
            if video:
                with open(video, 'rb') as f:
                    bot.send_video(message.chat.id, f)
                os.remove(video)
            else:
                bot.reply_to(message, "❌ Ошибка скачивания")

if __name__ == "__main__":
    print("Бот запущен!")
    bot.infinity_polling()
  
