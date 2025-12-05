import telebot
import subprocess
import os
import re
import glob
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

🌐 Сменить язык: /language''',
        'lang_choice': '🌐 Выберите язык:',
        'lang_set': '✅ Язык установлен: Русский',
        'error': '❌ Не удалось скачать. Попробуйте позже или проверьте ссылку.',
        'video_caption': 'Скачано с @tiktok27_bot 🎬',
        'audio_caption': 'Скачано с @tiktok27_bot 🎵',
        'photo_caption': 'Скачано с @tiktok27_bot 📷',
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

🌐 Change language: /language''',
        'lang_choice': '🌐 Choose language:',
        'lang_set': '✅ Language set: English',
        'error': '❌ Failed to download. Try again later or check the link.',
        'video_caption': 'Downloaded with @tiktok27_bot 🎬',
        'audio_caption': 'Downloaded with @tiktok27_bot 🎵',
        'photo_caption': 'Downloaded with @tiktok27_bot 📷',
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

🌐 Тілді өзгерту: /language''',
        'lang_choice': '🌐 Тілді таңдаңыз:',
        'lang_set': '✅ Тіл орнатылды: Қазақша',
        'error': '❌ Жүктеу мүмкін болмады. Кейінірек қайталаңыз.',
        'video_caption': '@tiktok27_bot арқылы жүктелді 🎬',
        'audio_caption': '@tiktok27_bot арқылы жүктелді 🎵',
        'photo_caption': '@tiktok27_bot арқылы жүктелді 📷',
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

🌐 Змінити мову: /language''',
        'lang_choice': '🌐 Оберіть мову:',
        'lang_set': '✅ Мову встановлено: Українська',
        'error': '❌ Не вдалося завантажити. Спробуйте пізніше.',
        'video_caption': 'Завантажено з @tiktok27_bot 🎬',
        'audio_caption': 'Завантажено з @tiktok27_bot 🎵',
        'photo_caption': 'Завантажено з @tiktok27_bot 📷',
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

🌐 Tilni o'zgartirish: /language''',
        'lang_choice': "🌐 Tilni tanlang:",
        'lang_set': "✅ Til o'rnatildi: O'zbekcha",
        'error': "❌ Yuklab bo'lmadi. Keyinroq urinib ko'ring.",
        'video_caption': '@tiktok27_bot orqali yuklandi 🎬',
        'audio_caption': '@tiktok27_bot orqali yuklandi 🎵',
        'photo_caption': '@tiktok27_bot orqali yuklandi 📷',
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

@bot.message_handler(commands=['language'])
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
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio/best[height<=1080]/best",
        "--merge-output-format", "mp4",
        "--postprocessor-args", "ffmpeg:-af loudnorm=I=-16:TP=-1.5:LRA=11",
        "-o", video_output,
        "--no-playlist",
        url
    ]
    try:
        subprocess.run(cmd, check=True, timeout=300, capture_output=True)
        if os.path.exists(video_output):
            return video_output
    except:
        pass
    return None

def download_photos(url):
    prefix = f"photo_{os.getpid()}"
    try:
        subprocess.run(
            ["yt-dlp", "-o", f"{prefix}_%(autonumber)s.%(ext)s", "--no-playlist", url],
            capture_output=True,
            timeout=300
        )
        photos = glob.glob(f"{prefix}_*.jpg") + glob.glob(f"{prefix}_*.jpeg") + glob.glob(f"{prefix}_*.png") + glob.glob(f"{prefix}_*.webp")
        if photos:
            return sorted(photos)
    except:
        pass
    return None

def download_audio(url):
    audio_output = f"audio_{os.getpid()}.mp3"
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--postprocessor-args", "ffmpeg:-af loudnorm=I=-16:TP=-1.5:LRA=11",
        "-o", audio_output,
        "--no-playlist",
        url
    ]
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
            
            # Просто эмодзи песочных часов
            status_msg = bot.send_message(chat_id, "⏳")
            
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
                photos = download_photos(url)
                if photos:
                    try:
                        media = []
                        for i, photo in enumerate(photos[:10]):
                            with open(photo, 'rb') as f:
                                if i == 0:
                                    media.append(telebot.types.InputMediaPhoto(f.read(), caption=get_text(user_id, 'photo_caption')))
                                else:
                                    media.append(telebot.types.InputMediaPhoto(f.read()))
                        
                        if media:
                            bot.send_media_group(chat_id, media)
                        
                        for photo in photos:
                            os.remove(photo)
                        
                        audio = download_audio(url)
                        if audio:
                            with open(audio, 'rb') as f:
                                bot.send_audio(chat_id, f, caption=get_text(user_id, 'audio_caption'))
                            os.remove(audio)
                    except:
                        bot.send_message(chat_id, get_text(user_id, 'error'))
                        for photo in photos:
                            if os.path.exists(photo):
                                os.remove(photo)
                else:
                    bot.send_message(chat_id, get_text(user_id, 'error'))
            
            try:
                bot.delete_message(chat_id, status_msg.message_id)
            except:
                pass

if __name__ == "__main__":
    print("Бот запущен!")
    bot.infinity_polling()
