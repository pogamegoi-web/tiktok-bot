import telebot
import yt_dlp
import os
import re
import requests

BOT_TOKEN = "8347415373:AAE86SZs9sHvHXIiNPv5h_1tPZf6hmLYGjI"
bot = telebot.TeleBot(BOT_TOKEN)

user_lang = {}

texts = {
    'ru': {
        'start': '👋 Привет! Отправь мне ссылку из TikTok',
        'downloading': '⏳ Скачиваю...',
        'success': '✅ Готово!',
        'error': '❌ Не удалось скачать',
        'lang_set': '✅ Русский'
    },
    'en': {
        'start': '👋 Hi! Send me a TikTok link',
        'downloading': '⏳ Downloading...',
        'success': '✅ Done!',
        'error': '❌ Failed to download',
        'lang_set': '✅ English'
    },
    'kz': {
        'start': '👋 Сәлем! TikTok сілтемесін жібер',
        'downloading': '⏳ Жүктелуде...',
        'success': '✅ Дайын!',
        'error': '❌ Жүктеу сәтсіз',
        'lang_set': '✅ Қазақша'
    },
    'ua': {
        'start': '👋 Привіт! Надішли посилання з TikTok',
        'downloading': '⏳ Завантажую...',
        'success': '✅ Готово!',
        'error': '❌ Не вдалося завантажити',
        'lang_set': '✅ Українська'
    },
    'uz': {
        'start': '👋 Salom! TikTok havolasini yubor',
        'downloading': '⏳ Yuklanmoqda...',
        'success': '✅ Tayyor!',
        'error': '❌ Yuklab bo\'lmadi',
        'lang_set': '✅ O\'zbek'
    }
}

def get_text(user_id, key):
    return texts[user_lang.get(user_id, 'ru')][key]

def get_tiktok_info(url):
    """Получает инфо через yt-dlp без скачивания"""
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except:
        return None

def download_video(url):
    try:
        for f in os.listdir('.'):
            if f.startswith('video.'):
                os.remove(f)
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video.%(ext)s',
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        for f in os.listdir('.'):
            if f.startswith('video.'):
                return f
    except:
        pass
    return None

def download_tiktok_photos(url):
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)'}
    
    # Сначала пробуем получить через yt-dlp
    try:
        info = get_tiktok_info(url)
        if info:
            photos = []
            
            # Ищем изображения в thumbnails
            for thumb in info.get('thumbnails', []):
                thumb_url = thumb.get('url', '')
                if thumb_url and thumb_url not in photos:
                    photos.append(thumb_url)
            
            # Ищем в других полях
            for key in ['thumbnail', 'cover']:
                if info.get(key):
                    photos.append(info[key])
            
            if photos:
                downloaded = []
                best_size = 0
                best_content = None
                
                for photo_url in photos:
                    try:
                        resp = requests.get(photo_url, headers=headers, timeout=30)
                        if resp.status_code == 200 and len(resp.content) > best_size:
                            best_size = len(resp.content)
                            best_content = resp.content
                    except:
                        continue
                
                if best_content and best_size > 5000:
                    with open('photo_0.jpg', 'wb') as f:
                        f.write(best_content)
                    return ['photo_0.jpg']
    except:
        pass
    
    # Fallback - парсим HTML
    try:
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        html = response.text
        
        photos = []
        patterns = [
            r'"imageURL"[^}]*"urlList":\s*\[\s*"([^"]+)"',
            r'"originCover":\s*"([^"]+)"',
            r'"cover":\s*"([^"]+)"',
            r'property="og:image"\s+content="([^"]+)"',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html)
            for m in matches:
                clean_url = m.replace('\\u002F', '/').replace('\\/', '/')
                if clean_url.startswith('http') and clean_url not in photos:
                    if 'avatar' not in clean_url.lower():
                        photos.append(clean_url)
        
        if not photos:
            return None
        
        downloaded = []
        seen_sizes = set()
        
        for i, photo_url in enumerate(photos[:15]):
            try:
                resp = requests.get(photo_url, headers=headers, timeout=30)
                if resp.status_code == 200:
                    size = len(resp.content)
                    if size < 10000 or size in seen_sizes:
                        continue
                    seen_sizes.add(size)
                    
                    filename = f"photo_{i}.jpg"
                    with open(filename, 'wb') as f:
                        f.write(resp.content)
                    downloaded.append(filename)
                    
                    if len(downloaded) >= 10:
                        break
            except:
                continue
        
        if len(downloaded) > 1:
            downloaded = downloaded[:-1]
        
        return downloaded if downloaded else None
    except:
        return None

def download_tiktok_audio(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)'}
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        html = response.text
        
        pattern = r'"playUrl":\s*"([^"]+)"'
        matches = re.findall(pattern, html)
        
        for m in matches:
            clean_url = m.replace('\\u002F', '/').replace('\\/', '/')
            if clean_url.startswith('http'):
                try:
                    resp = requests.get(clean_url, headers=headers, timeout=30)
                    if resp.status_code == 200 and len(resp.content) > 5000:
                        with open('audio.mp3', 'wb') as f:
                            f.write(resp.content)
                        return 'audio.mp3'
                except:
                    continue
        return None
    except:
        return None

def cleanup():
    for f in os.listdir('.'):
        if f.startswith(('video.', 'photo_', 'audio')) or f.endswith(('.mp4', '.jpg', '.mp3')):
            try:
                os.remove(f)
            except:
                pass

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        telebot.types.InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kz"),
        telebot.types.InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua"),
        telebot.types.InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz")
    )
    bot.send_message(message.chat.id, get_text(message.from_user.id, 'start'), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    lang = call.data.split('_')[1]
    user_lang[call.from_user.id] = lang
    bot.answer_callback_query(call.id, texts[lang]['lang_set'])
    bot.edit_message_text(texts[lang]['start'], call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    url = message.text.strip()
    user_id = message.from_user.id
    
    if 'tiktok.com' not in url.lower():
        return
    
    status = bot.reply_to(message, get_text(user_id, 'downloading'))
    cleanup()
    
    try:
        video = download_video(url)
        if video:
            with open(video, 'rb') as f:
                bot.send_video(message.chat.id, f)
            bot.edit_message_text(get_text(user_id, 'success'), message.chat.id, status.message_id)
        else:
            photos = download_tiktok_photos(url)
            if photos:
                if len(photos) == 1:
                    with open(photos[0], 'rb') as f:
                        bot.send_photo(message.chat.id, f)
                else:
                    media = [telebot.types.InputMediaPhoto(open(p, 'rb')) for p in photos]
                    bot.send_media_group(message.chat.id, media)
                
                audio = download_tiktok_audio(url)
                if audio:
                    with open(audio, 'rb') as f:
                        bot.send_audio(message.chat.id, f, title="TikTok Audio")
                
                bot.edit_message_text(get_text(user_id, 'success'), message.chat.id, status.message_id)
            else:
                bot.edit_message_text(get_text(user_id, 'error'), message.chat.id, status.message_id)
    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text(get_text(user_id, 'error'), message.chat.id, status.message_id)
    finally:
        cleanup()

if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling()
                    
