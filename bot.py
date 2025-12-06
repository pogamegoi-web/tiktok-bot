import telebot
from telebot.types import InputMediaPhoto
import yt_dlp
import requests
import os
import subprocess

BOT_TOKEN = "8347415373:AAE86SZs9sHvHXIiNPv5h_1tPZf6hmLYGjI"
bot = telebot.TeleBot(BOT_TOKEN)

BOT_USERNAME = "@tiktok27_bot"

TEXTS = {
    'ru': {'start': '👋 Привет! Отправь ссылку на TikTok видео или фото', 'error': '❌ Не удалось скачать'},
    'en': {'start': '👋 Hi! Send me a TikTok video or photo link', 'error': '❌ Failed to download'},
    'kk': {'start': '👋 Сәлем! TikTok видео немесе фото сілтемесін жіберіңіз', 'error': '❌ Жүктеу сәтсіз'},
    'uk': {'start': '👋 Привіт! Надішліть посилання на TikTok відео або фото', 'error': '❌ Не вдалося завантажити'},
    'uz': {'start': '👋 Salom! TikTok video yoki rasm havolasini yuboring', 'error': '❌ Yuklab bo\'lmadi'}
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
            return {'images': d.get('images', []), 'music': d.get('music')}
    except:
        pass
    return None

def download_video_yt(url):
    try:
        for f in os.listdir('.'):
            if f.startswith('video.') or f.startswith('audio.'):
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

def extract_audio(video_file):
    audio_file = 'audio.aac'
    try:
        subprocess.run([
            'ffmpeg', '-i', video_file, '-vn', '-acodec', 'copy', audio_file, '-y'
        ], capture_output=True, timeout=60)
        if os.path.exists(audio_file):
            return audio_file
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
    
    status = bot.send_message(chat_id, "⏳")
    
    try:
        data = download_via_tikwm(url)
        
        if data and data.get('images'):
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
                audio_file = download_audio(data['music'])
                if audio_file:
                    with open(audio_file, 'rb') as f:
                        bot.send_audio(chat_id, f, caption=caption, title="TikTok Audio", performer="TikTok")
                    os.remove(audio_file)
            
            bot.delete_message(chat_id, status.message_id)
            return
        
        video_file = download_video_yt(url)
        if video_file:
            with open(video_file, 'rb') as f:
                bot.send_video(chat_id, f, caption=caption)
            
            audio_file = extract_audio(video_file)
            if audio_file:
                with open(audio_file, 'rb') as f:
                    bot.send_audio(chat_id, f, caption=caption, title="TikTok Audio", performer="TikTok")
                os.remove(audio_file)
            
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
    
