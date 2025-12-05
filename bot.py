import telebot
import subprocess
import os
import re
from config import BOT_TOKEN, ADMIN_ID

bot = telebot.TeleBot(BOT_TOKEN)

user_lang = {}

texts = {
    'ru': {
        'start': '''🎬 Video Downloader Bot

Привет! Я могу скачать видео из:
• TikTok
• Instagram Reels
• YouTube Shorts

✨ Без водяного знака и в HD!

Как использовать:
Просто отправь мне ссылку на видео!

🌐 Сменить язык: /lang''',
        'lang_choice': '🌐 Выберите язык:',
        'lang_set': '✅ Язык установлен: Русский',
        'downloading': '⏳ Скачиваю...',
        'error': '❌ Не удалось скачать видео. Попробуйте позже или проверьте ссылку.',
        'video_caption': 'Скачано с @tiktok27_bot 🎬',
        'audio_caption': 'Скачано с @tiktok27_bot 🎵',
        'too_big': '⚠️ Видео слишком большое для Telegram (макс 50 МБ)'
    },
    'en': {
        'start': '''🎬 Video Downloader Bot

Hi! I can download videos from:
• TikTok
• Instagram Reels
• YouTube Shorts

✨ Without watermark and in HD!

How to use:
Just send me a link to the video!

🌐 Change language: /lang''',
        'lang_choice': '🌐 Choose language:',
        'lang_set': '✅ Language set: English',
        'downloading': '⏳ Downloading...',
        'error': '❌ Failed to download video. Try again later or check the link.',
        'video_caption': 'Downloaded with @tiktok27_bot 🎬',
        'audio_caption': 'Downloaded with @tiktok27_bot 🎵',
        'too_big': '⚠️ Video is too large for Telegram (max 50 MB)'
    },
    'kz': {
        'start': '''🎬 Video Downloader Bot

Сәлем! Мен видео жүктей аламын:
• TikTok
• Instagram Reels
• YouTube Shorts

✨ Су белгісіз және HD сапада!

Қалай қолдану керек:
Маған видеоға сілтеме жіберіңіз!

🌐 Тілді өзгерту: /lang''',
        'lang_choice': '🌐 Тілді таңдаңыз:',
        'lang_set': '✅ Тіл орнатылды: Қазақша',
        'downloading': '⏳ Жүктелуде...',
        'error': '❌ Видеоны жүктеу мүмкін болмады. Кейінірек қайталаңыз.',
        'video_caption': '@tiktok27_bot арқылы жүктелді 🎬',
        'audio_caption': '@tiktok27_bot арқылы жүктелді 🎵',
        'too_big': '⚠️ Видео Telegram үшін тым үлкен (макс 50 МБ)'
    },
    'ua': {
        'start': '''🎬 Video Downloader Bot

Привіт! Я можу завантажити відео з:
• TikTok
• Instagram Reels
• YouTube Shorts

✨ Без водяного знаку та в HD!

Як використовувати:
Просто надішли мені посилання на відео!

🌐 Змінити мову: /lang''',
        'lang_choice': '🌐 Оберіть мову:',
        'lang_set': '✅ Мову встановлено: Українська',
        'downloading': '⏳ Завантажую...',
        'error': '❌ Не вдалося завантажити відео. Спробуйте пізніше.',
        'video_caption': 'Завантажено з @tiktok27_bot 🎬',
        'audio_caption': 'Завантажено з @tiktok27_bot 🎵',
        'too_big': '⚠️ Відео занадто велике для Telegram (макс 50 МБ)'
    },
    'uz': {
        'start': '''🎬 Video Downloader Bot

Salom! Men video yuklay olaman:
• TikTok
• Instagram Reels
• YouTube Shorts

✨ Suv belgisisiz va HD sifatda!

Qanday foydalanish:
Menga videoga havola yuboring!

🌐 Tilni o'zgartirish: /lang''',
        'lang_choice': "🌐 Tilni tanlang:",
        'lang_set': "✅ Til o'rnatildi: O'zbekcha",
        'downloading': '⏳ Yuklanmoqda...',
        'error': "❌ Videoni yuklab bo'lmadi. Keyinroq urinib ko'ring.",
        'video_caption': '@tiktok27_bot orqali yuklandi 🎬',
        'audio_caption': '@tiktok27_bot orqali yuklandi 🎵',
        'too_big': '⚠️ Video Telegram uchun juda katta (maks 50 MB)'
    }
}

def get_text(user_id, key):
    lang = user_lang.get(user_id, 'ru')
    return texts[lang][key]

@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_lang.setdefault(message.from_user.id, 'ru')
    bot.send_message(message.chat.id, get_text(message.from_user.id, 'start'))

@bot.message_handler(commands=['lang'])
def cmd_lang(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        telebot.types.InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kz"),
        telebot.types.InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua"),
        telebot.types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")
    )
    bot.send_message(message.chat.id, get_text(message.from_user.id, 'lang_choice'), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def callback_lang(call):
    lang = call.data.split('_')[1]
    user_lang[call.from_user.id] = lang
    bot.answer_callback_query(call.id)
    bot.edit_message_text(get_text(call.from_user.id, 'lang_set'), call.message.chat.id, call.message.message_id)

def download_video(url):
    video_output = f"video_{os.getpid()}.mp4"
    cmd = ["yt-dlp", "-f", "best[ext=mp4]/best", "-o", video_output, "--no-playlist", url]
    try:
        subprocess.run(cmd, check=True, timeout=300, capture_output=True)
        if os.path.exists(video_output):
            return video_output
    except:
        pass
    return None

def download_audio(url):
    audio_output = f"audio_{os.getpid()}.mp3"
    cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", audio_output, "--no-playlist", url]
    try:
        subprocess.run(cmd, check=True, timeout=300, capture_output=True)
        if os.path.exists(audio_output):
            return audio_output
    except:
        pass
    return None

@bot.message_handler(func=lambda m: True)
def handle(message):
    text = message.text or ""
    urls = re.findall(r'https?://[^\s]+', text)
    for url in urls:
        if any(x in url for x in ['tiktok.com', 'instagram.com', 'youtube.com', 'youtu.be']):
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            try:
                bot.delete_message(chat_id, message.message_id)
            except:
                pass
            
            status_msg = bot.send_message(chat_id, get_text(user_id, 'downloading'))
            
            video = download_video(url)
            if video:
                try:
                    size = os.path.getsize(video) / (1024 * 1024)
                    if size > 50:
                        bot.send_message(chat_id, get_text(user_id, 'too_big'))
                    else:
                        with open(video, 'rb') as f:
                            bot.send_video(chat_id, f, caption=get_text(user_id, 'video_caption'), supports_streaming=True)
                    os.remove(video)
                    audio = download_audio(url)
                    if audio:
                        with open(audio, 'rb') as f:
                            bot.send_audio(chat_id, f, caption=get_text(user_id, 'audio_caption'))
                        os.remove(audio)
                except:
                    bot.send_message(chat_id, get_text(user_id, 'error'))
                    if os.path.exists(video):
                        os.remove(video)
            else:
                bot.send_message(chat_id, get_text(user_id, 'error'))
            
            try:
                bot.delete_message(chat_id, status_msg.message_id)
            except:
                pass

if __name__ == "__main__":
    print("Бот запущен!")
    bot.infinity_polling()
    
