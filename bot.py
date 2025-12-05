import telebot
import subprocess
import os
import re
from config import BOT_TOKEN, ADMIN_ID

bot = telebot.TeleBot(BOT_TOKEN)

# Хранение языка пользователей
user_lang = {}

texts = {
    'ru': {
        'start': '👋 Привет! Отправь мне ссылку на видео из TikTok, Instagram или YouTube, и я скачаю его для тебя.\n\n🌐 Сменить язык: /lang',
        'lang_choice': '🌐 Выбери язык / Choose language:',
        'lang_set': '✅ Язык установлен: Русский',
        'downloading': '⏳ Скачиваю...',
        'error': '❌ Ошибка скачивания',
        'too_big': '⚠️ Видео слишком большое для Telegram (макс 50 МБ)'
    },
    'en': {
        'start': '👋 Hi! Send me a link to a video from TikTok, Instagram or YouTube, and I will download it for you.\n\n🌐 Change language: /lang',
        'lang_choice': '🌐 Выбери язык / Choose language:',
        'lang_set': '✅ Language set: English',
        'downloading': '⏳ Downloading...',
        'error': '❌ Download error',
        'too_big': '⚠️ Video is too large for Telegram (max 50 MB)'
    }
}

def get_text(user_id, key):
    lang = user_lang.get(user_id, 'ru')
    return texts[lang][key]

@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_lang.setdefault(message.from_user.id, 'ru')
    bot.reply_to(message, get_text(message.from_user.id, 'start'))

@bot.message_handler(commands=['lang'])
def cmd_lang(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    bot.reply_to(message, get_text(message.from_user.id, 'lang_choice'), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def callback_lang(call):
    lang = call.data.split('_')[1]
    user_lang[call.from_user.id] = lang
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        get_text(call.from_user.id, 'lang_set'),
        call.message.chat.id,
        call.message.message_id
    )

def download_video(url):
    output = f"video_{os.getpid()}.mp4"
    cmd = ["yt-dlp", "-f", "best[ext=mp4]/best", "-o", output, "--no-playlist", url]
    try:
        subprocess.run(cmd, check=True, timeout=300)
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
        if any(x in url for x in ['tiktok.com', 'instagram.com', 'youtube.com', 'youtu.be']):
            bot.reply_to(message, get_text(message.from_user.id, 'downloading'))
            video = download_video(url)
            
            if video:
                size = os.path.getsize(video) / (1024 * 1024)
                if size > 50:
                    bot.reply_to(message, get_text(message.from_user.id, 'too_big'))
                else:
                    with open(video, 'rb') as f:
                        bot.send_video(message.chat.id, f)
                os.remove(video)
            else:
                bot.reply_to(message, get_text(message.from_user.id, 'error'))

if __name__ == "__main__":
    print("Бот запущен!")
    bot.infinity_polling()
    
