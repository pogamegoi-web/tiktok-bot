import telebot
import yt_dlp
import os
import subprocess
import json
import re
import requests

BOT_TOKEN = "8347415373:AAE86SZs9sHvHXIiNPv5h_1tPZf6hmLYGjI"
ADMIN_ID = 6272691860
FACEBOOK_COOKIES = "facebook_cookies.txt"

bot = telebot.TeleBot(BOT_TOKEN)
user_lang = {}

texts = {
    'ru': {'start': '👋 Привет! Отправь мне ссылку на видео или фото из:\n\n• TikTok (видео, фото, истории)\n• Instagram (видео, фото, истории, Reels)\n• YouTube (видео, Shorts)\n• Facebook (видео, фото, истории)\n\n📹 Видео в HD 1080p\n🎵 Музыка отдельно', 'downloading': '⏳ Скачиваю...', 'success': '✅ Готово!', 'error': '❌ Ошибка', 'invalid_link': '❌ Неверная ссылка', 'lang_set': '✅ Русский'},
    'en': {'start': '👋 Hi! Send me a link from:\n\n• TikTok\n• Instagram\n• YouTube\n• Facebook\n\n📹 HD 1080p\n🎵 Music separately', 'downloading': '⏳ Downloading...', 'success': '✅ Done!', 'error': '❌ Error', 'invalid_link': '❌ Invalid link', 'lang_set': '✅ English'},
    'kz': {'start': '👋 Сәлем! Сілтеме жібер:\n\n• TikTok\n• Instagram\n• YouTube\n• Facebook', 'downloading': '⏳ Жүктелуде...', 'success': '✅ Дайын!', 'error': '❌ Қате', 'invalid_link': '❌ Қате сілтеме', 'lang_set': '✅ Қазақша'},
    'ua': {'start': '👋 Привіт! Надішли посилання:\n\n• TikTok\n• Instagram\n• YouTube\n• Facebook', 'downloading': '⏳ Завантажую...', 'success': '✅ Готово!', 'error': '❌ Помилка', 'invalid_link': '❌ Невірне посилання', 'lang_set': '✅ Українська'},
    'uz': {'start': '👋 Salom! Havola yubor:\n\n• TikTok\n• Instagram\n• YouTube\n• Facebook', 'downloading': '⏳ Yuklanmoqda...', 'success': '✅ Tayyor!', 'error': '❌ Xato', 'invalid_link': '❌ Noto\'g\'ri havola', 'lang_set': '✅ O\'zbek'}
}

def get_text(user_id, key):
    return texts[user_lang.get(user_id, 'ru')][key]

def get_video_info(path):
    try:
        r = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', '-show_format', path], capture_output=True, text=True)
        d = json.loads(r.stdout)
        w, h, dur = None, None, None
        for s in d.get('streams', []):
            if s.get('codec_type') == 'video':
                w, h = s.get('width'), s.get('height')
                break
        if 'format' in d and d['format'].get('duration'):
            dur = int(float(d['format']['duration']))
        return w, h, dur
    except:
        return None, None, None

def get_audio_duration(path):
    try:
        r = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', path], capture_output=True, text=True)
        d = json.loads(r.stdout)
        if 'format' in d and d['format'].get('duration'):
            return int(float(d['format']['duration']))
    except:
        pass
    return None

def extract_audio(video_path):
    try:
        audio_path = "audio_extracted.mp3"
        subprocess.run(['ffmpeg', '-y', '-i', video_path, '-vn', '-acodec', 'libmp3lame', '-ab', '192k', audio_path], capture_output=True, timeout=120)
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
            return audio_path
    except:
        pass
    return None

def download_tiktok_audio(url):
    """Скачивает музыку из TikTok слайдшоу"""
    try:
        # Удаляем старые файлы
        for f in os.listdir('.'):
            if f.startswith('slideshow_') or f.startswith('tiktok_audio'):
                try: os.remove(f)
                except: pass
        
        # Скачиваем слайдшоу как видео
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'slideshow_video.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Ищем скачанный файл
        video_file = None
        for f in os.listdir('.'):
            if f.startswith('slideshow_video'):
                video_file = f
                break
        
        if not video_file:
            return None
        
        # Извлекаем аудио
        audio_path = "tiktok_audio.mp3"
        subprocess.run(['ffmpeg', '-y', '-i', video_file, '-vn', '-acodec', 'libmp3lame', '-ab', '192k', audio_path], capture_output=True, timeout=120)
        
        # Удаляем видео
        try: os.remove(video_file)
        except: pass
        
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
            return audio_path
        return None
    except Exception as e:
        print(f"Audio error: {e}")
        return None

def get_facebook_cookies():
    cookies = {}
    if os.path.exists(FACEBOOK_COOKIES):
        try:
            with open(FACEBOOK_COOKIES, 'r') as f:
                for line in f:
                    if not line.startswith('#') and line.strip():
                        parts = line.strip().split('\t')
                        if len(parts) >= 7:
                            cookies[parts[5]] = parts[6]
        except: pass
    return cookies

def is_valid_url(url):
    return any(p in url.lower() for p in ['tiktok.com', 'vm.tiktok.com', 'instagram.com', 'youtube.com', 'youtu.be', 'facebook.com', 'fb.watch'])

def is_tiktok_url(url):
    return 'tiktok.com' in url.lower() or 'vm.tiktok.com' in url.lower()

def is_instagram_url(url):
    return 'instagram.com' in url.lower()

def is_youtube_url(url):
    return 'youtube.com' in url.lower() or 'youtu.be' in url.lower()

def is_facebook_url(url):
    return 'facebook.com' in url.lower() or 'fb.watch' in url.lower()

def download_tiktok_photos(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'}
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        html = response.text
        photos = []
        for match in re.findall(r'"imageURL":\s*\{[^}]*"urlList":\s*\[\s*"([^"]+)"', html):
            clean_url = match.replace('\\u002F', '/').replace('\\/', '/')
            if clean_url.startswith('http') and clean_url not in photos:
                if 'cover' not in clean_url.lower() and 'thumb' not in clean_url.lower():
                    photos.append(clean_url)
        if not photos:
            return None
        downloaded = []
        seen_sizes = set()
        for i, photo_url in enumerate(photos[:10]):
            try:
                resp = requests.get(photo_url, headers=headers, timeout=30)
                if resp.status_code == 200 and len(resp.content) > 5000:
                    size = len(resp.content)
                    if size not in seen_sizes:
                        seen_sizes.add(size)
                        ext = 'webp' if 'webp' in photo_url else 'jpg'
                        filename = f"tiktok_photo_{i}.{ext}"
                        with open(filename, 'wb') as f:
                            f.write(resp.content)
                        downloaded.append(filename)
            except: continue
        return downloaded if downloaded else None
    except:
        return None

def download_instagram_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'}
        response = requests.get(url, headers=headers, timeout=30)
        html = response.text
        photos, videos, downloaded = [], [], []
        for pattern in [r'"display_url":\s*"([^"]+)"', r'property="og:image"\s+content="([^"]+)"']:
            for match in re.findall(pattern, html):
                clean = match.replace('\\u0026', '&').replace('\\/', '/')
                if ('instagram' in clean or 'cdninstagram' in clean) and clean not in photos:
                    photos.append(clean)
        for pattern in [r'"video_url":\s*"([^"]+)"', r'property="og:video"\s+content="([^"]+)"']:
            for match in re.findall(pattern, html):
                clean = match.replace('\\u0026', '&').replace('\\/', '/')
                if clean not in videos:
                    videos.append(clean)
        for i, v in enumerate(videos[:3]):
            try:
                resp = requests.get(v, headers=headers, timeout=60)
                if resp.status_code == 200:
                    fn = f"instagram_video_{i}.mp4"
                    with open(fn, 'wb') as f: f.write(resp.content)
                    downloaded.append(('video', fn))
            except: continue
        seen = set()
        for i, p in enumerate(photos[:10]):
            try:
                resp = requests.get(p, headers=headers, timeout=30)
                if resp.status_code == 200:
                    size = len(resp.content)
                    if size > 10000 and size not in seen:
                        seen.add(size)
                        fn = f"instagram_photo_{i}.jpg"
                        with open(fn, 'wb') as f: f.write(resp.content)
                        downloaded.append(('photo', fn))
            except: continue
        return downloaded if downloaded else None
    except:
        return None

def download_facebook_content(url):
    try:
        cookies = get_facebook_cookies()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
        html = response.text
        photos, videos, downloaded = [], [], []
        for pattern in [r'"playable_url_quality_hd":\s*"([^"]+)"', r'"playable_url":\s*"([^"]+)"', r'"hd_src":\s*"([^"]+)"', r'"sd_src":\s*"([^"]+)"']:
            for match in re.findall(pattern, html):
                clean = match.replace('\\/', '/').replace('\\u0025', '%').replace('\\u0026', '&')
                if clean.startswith('http') and clean not in videos:
                    videos.append(clean)
        for pattern in [r'"image":\s*\{[^}]*"uri":\s*"([^"]+scontent[^"]+)"', r'property="og:image"\s+content="([^"]+)"']:
            for match in re.findall(pattern, html):
                clean = match.replace('\\/', '/').replace('\\u0025', '%').replace('\\u0026', '&')
                if 'scontent' in clean and clean not in photos:
                    photos.append(clean)
        for v in videos[:1]:
            try:
                resp = requests.get(v, headers=headers, cookies=cookies, timeout=120)
                if resp.status_code == 200 and len(resp.content) > 10000:
                    with open("facebook_video_0.mp4", 'wb') as f: f.write(resp.content)
                    downloaded.append(('video', "facebook_video_0.mp4"))
                    break
            except: continue
        seen = set()
        for i, p in enumerate(photos[:10]):
            try:
                resp = requests.get(p, headers=headers, timeout=30)
                if resp.status_code == 200:
                    size = len(resp.content)
                    if size > 20000 and size not in seen:
                        seen.add(size)
                        fn = f"facebook_photo_{i}.jpg"
                        with open(fn, 'wb') as f: f.write(resp.content)
                        downloaded.append(('photo', fn))
            except: continue
        return downloaded if downloaded else None
    except:
        return None

def download_video(url):
    ydl_opts = {'format': 'best[height<=1080]/best', 'outtmpl': 'video.%(ext)s', 'quiet': True, 'no_warnings': True, 'socket_timeout': 60, 'retries': 5}
    if is_youtube_url(url):
        ydl_opts.update({'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best', 'merge_output_format': 'mp4'})
    if is_facebook_url(url) and os.path.exists(FACEBOOK_COOKIES):
        ydl_opts['cookiefile'] = FACEBOOK_COOKIES
    try:
        for f in os.listdir('.'):
            if f.startswith('video.'): os.remove(f)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        for f in os.listdir('.'):
            if f.startswith('video.'): return f
        return None
    except:
        return None

def cleanup_files():
    for f in os.listdir('.'):
        if any([f.startswith('video.'), f.startswith('tiktok_'), f.startswith('instagram_'), f.startswith('facebook_'), f.startswith('slideshow_'), f.startswith('audio_'), f.endswith('.mp4'), f.endswith('.mp3'), f.endswith('.jpg'), f.endswith('.webp')]):
            try: os.remove(f)
            except: pass

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
    if not is_valid_url(url):
        bot.reply_to(message, get_text(user_id, 'invalid_link'))
        return
    status_msg = bot.reply_to(message, get_text(user_id, 'downloading'))
    try:
        cleanup_files()
        success = False
        
        if is_tiktok_url(url):
            video_path = download_video(url)
            if video_path:
                w, h, dur = get_video_info(video_path)
                with open(video_path, 'rb') as f:
                    bot.send_video(message.chat.id, f, supports_streaming=True, width=w, height=h, duration=dur)
                audio = extract_audio(video_path)
                if audio:
                    with open(audio, 'rb') as f:
                        bot.send_audio(message.chat.id, f, duration=get_audio_duration(audio))
                success = True
            else:
                photos = download_tiktok_photos(url)
                if photos:
                    if len(photos) == 1:
                        with open(photos[0], 'rb') as f:
                            bot.send_photo(message.chat.id, f)
                    else:
                        media = [telebot.types.InputMediaPhoto(open(p, 'rb')) for p in photos[:10]]
                        bot.send_media_group(message.chat.id, media)
                    # Музыка для слайдшоу
                    audio = download_tiktok_audio(url)
                    if audio:
                        with open(audio, 'rb') as f:
                            bot.send_audio(message.chat.id, f, duration=get_audio_duration(audio))
                    success = True
        
        elif is_instagram_url(url):
            content = download_instagram_content(url)
            if content:
                for t, p in content:
                    if t == 'video':
                        w, h, dur = get_video_info(p)
                        with open(p, 'rb') as f:
                            bot.send_video(message.chat.id, f, supports_streaming=True, width=w, height=h, duration=dur)
                        success = True
                photos = [p for t, p in content if t == 'photo']
                if photos:
                    if len(photos) == 1:
                        with open(photos[0], 'rb') as f:
                            bot.send_photo(message.chat.id, f)
                    else:
                        media = [telebot.types.InputMediaPhoto(open(p, 'rb')) for p in photos[:10]]
                        bot.send_media_group(message.chat.id, media)
                    success = True
            if not success:
                video_path = download_video(url)
                if video_path:
                    w, h, dur = get_video_info(video_path)
                    with open(video_path, 'rb') as f:
                        bot.send_video(message.chat.id, f, supports_streaming=True, width=w, height=h, duration=dur)
                    success = True
        
        elif is_facebook_url(url):
            content = download_facebook_content(url)
            if content:
                for t, p in content:
                    if t == 'video':
                        w, h, dur = get_video_info(p)
                        with open(p, 'rb') as f:
                            bot.send_video(message.chat.id, f, supports_streaming=True, width=w, height=h, duration=dur)
                        success = True
                photos = [p for t, p in content if t == 'photo']
                if photos:
                    if len(photos) == 1:
                        with open(photos[0], 'rb') as f:
                            bot.send_photo(message.chat.id, f)
                    else:
                        media = [telebot.types.InputMediaPhoto(open(p, 'rb')) for p in photos[:10]]
                        bot.send_media_group(message.chat.id, media)
                    success = True
            if not success:
                video_path = download_video(url)
                if video_path:
                    w, h, dur = get_video_info(video_path)
                    with open(video_path, 'rb') as f:
                        bot.send_video(message.chat.id, f, supports_streaming=True, width=w, height=h, duration=dur)
                    success = True
        
        elif is_youtube_url(url):
            video_path = download_video(url)
            if video_path:
                w, h, dur = get_video_info(video_path)
                with open(video_path, 'rb') as f:
                    bot.send_video(message.chat.id, f, supports_streaming=True, width=w, height=h, duration=dur)
                success = True
        
        try: bot.delete_message(message.chat.id, message.message_id)
        except: pass
        
        bot.edit_message_text(get_text(user_id, 'success' if success else 'error'), message.chat.id, status_msg.message_id)
    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text(get_text(user_id, 'error'), message.chat.id, status_msg.message_id)
    finally:
        cleanup_files()

if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling()
            
