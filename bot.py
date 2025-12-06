import telebot
from telebot.types import InputMediaPhoto
import yt_dlp
import requests
import os

BOT_TOKEN = "8347415373:AAE86SZs9sHvHXIiNPv5h_1tPZf6hmLYGjI"
bot = telebot.TeleBot(BOT_TOKEN)

BOT_USERNAME = "@tiktok27_bot"

TEXTS = {
    'ru': {'start': '👋 Привет! Отправь ссылку на TikTok видео или фото', 'downloading': '⏳ Загружаю в HD...', 'error': '❌ Не удалось скачать'},
    'en': {'start': '👋 Hi! Send me a TikTok video or photo link', 'downloading': '⏳ Downloading in HD...', 'error': '❌ Failed to download'},
    'kk': {'start': '👋 Сәлем! TikTok видео немесе фото сілтемесін жіберіңіз', 'downloading': '⏳ HD жүктеп алуда...', 'error': '❌ Жүктеу сәтсіз'},
    'uk': {'start': '👋 Привіт! Надішліть посилання на TikTok відео або фото', 'downloading': '⏳ Завантажую в HD...', 'error': '❌ Не вдалося завантажити'},
    'uz': {'start': '👋 Salom! TikTok video yoki rasm havolasini yuboring', 'downloading': '⏳ HD yuklanmoqda...', 'error': '❌ Yuklab bo\'lmadi'}
}

def get_text(user, key):
    lang = getattr(user, 'language_code', 'en') or 'en'
    return TEXTS.get(lang, TEXTS['en']).get(key, TEXTS['en'][key])

def download_via_tikwm(url):
    try:
        api_url = f"https://www.tikwm.com/api/?url={url}&hd=1"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(api_url, headers=headers, timeout=10)
        data = resp.json()
        if data.get('code') == 0:
            d = data.get('data', {})
            return {
                'images': d.get('images', []),
                'music': d.get('music'),
                'hdplay': d.get('hdplay'),
                'play': d.get('play')
            }
    except:
        pass
    return None

def download_audio(url):
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        with open('audio.mp3', 'wb') as f:
            f.write(resp.content)
        return 'audio.mp3'
    except:
        return None

def download_video_hd(url):
    try:
        for f in os.listdir('.'):
            if f.startswith('video.'):
                os.remove(f)
    except:
        pass
    
    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
        'outtmpl': 'video.%(ext)s',
        'quiet': True,
        'merge_output_format': 'mp4'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        for f in os.listdir('.'):
            if f.startswith('video.'):
                return f
    except:
        pass
    return None

def send_audio(chat_id, music_url, caption):
    audio_file = download_audio(music_url)
    if audio_file:
        try:
            with open(audio_file, 'rb') as f:
                bot.send_audio(chat_id, f, caption=caption, title="TikTok Audio", performer="TikTok")
        except:
            pass
        try:
            os.remove(audio_file)
        except:
            pass

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, get_text(message.from_user, 'start'))

@bot.message_handler(func=lambda m: 'tiktok.com' in m.text.lower() if m.text else False)
def handle_tiktok(message):
    url = message.text.strip()
    user = message.from_user
    chat_id = message.chat.id
    caption = f"Скачано с {BOT_USERNAME}"
    
    try:
        bot.delete_message(chat_id, message.message_id)
    except:
        pass
    
    status = bot.send_message(chat_id, get_text(user, 'downloading'))
    
    try:
        data = download_via_tikwm(url)
        
        if data:
            if data.get('images'):
                photos = data['images']
                
                media = []
                for i, photo_url in enumerate(photos):
                    if i == 0:
                        media.append(InputMediaPhoto(photo_url, caption=caption))
                    else:
                        media.append(InputMediaPhoto(photo_url))
                
                try:
                    bot.send_media_group(chat_id, media)
                except:
                    for photo_url in photos:
                        bot.send_photo(chat_id, photo_url)
                
                if data.get('music'):
                    send_audio(chat_id, data['music'], caption)
                
                bot.delete_message(chat_id, status.message_id)
                return
            
            video_url = data.get('hdplay') or data.get('play')
            if video_url:
                try:
                    bot.send_video(chat_id, video_url, caption=caption)
                    
                    if data.get('music'):
                        send_audio(chat_id, data['music'], caption)
                    
                    bot.delete_message(chat_id, status.message_id)
                    return
                except:
                    pass
        
        video_file = download_video_hd(url)
        if video_file:
            with open(video_file, 'rb') as f:
                bot.send_video(chat_id, f, caption=caption)
            os.remove(video_file)
            bot.delete_message(chat_id, status.message_id)
            return
        
        bot.delete_message(chat_id, status.message_id)
        bot.send_message(chat_id, get_text(user, 'error'))
        
    except:
        bot.delete_message(chat_id, status.message_id)
        bot.send_message(chat_id, get_text(user, 'error'))

if __name__ == "__main__":
    bot.polling(none_stop=True)
    
