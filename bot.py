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
    'ru': {
        'start': '👋 Привет! Отправь мне ссылку на видео или фото из:\n\n• TikTok (видео, фото, истории)\n• Instagram (видео, фото, истории, Reels)\n• YouTube (видео, Shorts)\n• Facebook (видео, фото, истории)\n\n📹 Видео скачиваются в HD 1080p\n🎵 Музыка отправляется отдельно',
        'downloading': '⏳ Скачиваю...',
        'success': '✅ Готово!',
        'error': '❌ Не удалось скачать. Проверь ссылку.',
        'invalid_link': '❌ Отправь корректную ссылку',
        'lang_set': '✅ Язык изменён на Русский'
    },
    'en': {
        'start': '👋 Hi! Send me a link to video or photo from:\n\n• TikTok (videos, photos, stories)\n• Instagram (videos, photos, stories, Reels)\n• YouTube (videos, Shorts)\n• Facebook (videos, photos, stories)\n\n📹 Videos downloaded in HD 1080p\n🎵 Music sent separately',
        'downloading': '⏳ Downloading...',
        'success': '✅ Done!',
        'error': '❌ Failed to download. Check the link.',
        'invalid_link': '❌ Send a valid link',
        'lang_set': '✅ Language changed to English'
    },
    'kz': {
        'start': '👋 Сәлем! Маған видео немесе фото сілтемесін жібер:\n\n• TikTok (видео, фото, stories)\n• Instagram (видео, фото, stories, Reels)\n• YouTube (видео, Shorts)\n• Facebook (видео, фото, stories)\n\n📹 Видео HD 1080p форматында жүктеледі\n🎵 Музыка бөлек жіберіледі',
        'downloading': '⏳ Жүктелуде...',
        'success': '✅ Дайын!',
        'error': '❌ Жүктеу сәтсіз. Сілтемені тексер.',
        'invalid_link': '❌ Дұрыс сілтеме жібер',
        'lang_set': '✅ Тіл Қазақшаға өзгертілді'
    },
    'ua': {
        'start': '👋 Привіт! Надішли мені посилання на відео або фото з:\n\n• TikTok (відео, фото, історії)\n• Instagram (відео, фото, історії, Reels)\n• YouTube (відео, Shorts)\n• Facebook (відео, фото, історії)\n\n📹 Відео завантажуються в HD 1080p\n🎵 Музика надсилається окремо',
        'downloading': '⏳ Завантажую...',
        'success': '✅ Готово!',
        'error': '❌ Не вдалося завантажити. Перевір посилання.',
        'invalid_link': '❌ Надішли коректне посилання',
        'lang_set': '✅ Мову змінено на Українську'
    },
    'uz': {
        'start': '👋 Salom! Menga video yoki rasm havolasini yubor:\n\n• TikTok (video, rasm, stories)\n• Instagram (video, rasm, stories, Reels)\n• YouTube (video, Shorts)\n• Facebook (video, rasm, stories)\n\n📹 Videolar HD 1080p formatida yuklanadi\n🎵 Musiqa alohida yuboriladi',
        'downloading': '⏳ Yuklanmoqda...',
        'success': '✅ Tayyor!',
        'error': '❌ Yuklab bo\'lmadi. Havolani tekshir.',
        'invalid_link': '❌ To\'g\'ri havola yubor',
        'lang_set': '✅ Til O\'zbekchaga o\'zgartirildi'
    }
}

def get_text(user_id, key):
    lang = user_lang.get(user_id, 'ru')
    return texts[lang][key]

def get_video_info(video_path):
    """Получает метаданные видео через ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', '-show_format', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        width, height, duration = None, None, None
        
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                width = stream.get('width')
                height = stream.get('height')
                break
        
        if 'format' in data:
            dur = data['format'].get('duration')
            if dur:
                duration = int(float(dur))
        
        return width, height, duration
    except:
        return None, None, None

def extract_audio(video_path):
    """Извлекает аудио из видео в MP3"""
    try:
        audio_path = "audio_extracted.mp3"
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vn', '-acodec', 'libmp3lame', '-ab', '192k',
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
            return audio_path
    except:
        pass
    return None

def get_audio_duration(audio_path):
    """Получает длительность аудио"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        if 'format' in data:
            dur = data['format'].get('duration')
            if dur:
                return int(float(dur))
    except:
        pass
    return None

def download_tiktok_audio(url):
    """Скачивает музыку из TikTok слайдшоу"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
        }
        
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        html = response.text
        
        # Ищем URL музыки в HTML
        audio_urls = []
        
        # Паттерн для playUrl музыки
        patterns = [
            r'"playUrl":\s*"([^"]+)"',
            r'"music"[^}]*"playUrl":\s*"([^"]+)"',
            r'"audio"[^}]*"url":\s*"([^"]+)"',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html)
            for m in matches:
                clean_url = m.replace('\\u002F', '/').replace('\\/', '/')
                if clean_url.startswith('http') and clean_url not in audio_urls:
                    audio_urls.append(clean_url)
        
        # Скачиваем первый найденный аудио файл
        for audio_url in audio_urls:
            try:
                resp = requests.get(audio_url, headers=headers, timeout=30)
                if resp.status_code == 200 and len(resp.content) > 5000:
                    audio_path = "tiktok_audio.mp3"
                    with open(audio_path, 'wb') as f:
                        f.write(resp.content)
                    return audio_path
            except:
                continue
        
        return None
    except Exception as e:
        print(f"Audio error: {e}")
        return None
        
def get_facebook_cookies():
    """Загружает куки Facebook для requests"""
    cookies = {}
    if os.path.exists(FACEBOOK_COOKIES):
        try:
            with open(FACEBOOK_COOKIES, 'r') as f:
                for line in f:
                    if not line.startswith('#') and line.strip():
                        parts = line.strip().split('\t')
                        if len(parts) >= 7:
                            cookies[parts[5]] = parts[6]
        except:
            pass
    return cookies

def is_valid_url(url):
    platforms = ['tiktok.com', 'vm.tiktok.com', 'instagram.com', 
                 'youtube.com', 'youtu.be', 'facebook.com', 'fb.watch']
    return any(p in url.lower() for p in platforms)

def is_tiktok_url(url):
    return 'tiktok.com' in url.lower() or 'vm.tiktok.com' in url.lower()

def is_instagram_url(url):
    return 'instagram.com' in url.lower()

def is_youtube_url(url):
    return 'youtube.com' in url.lower() or 'youtu.be' in url.lower()

def is_facebook_url(url):
    return 'facebook.com' in url.lower() or 'fb.watch' in url.lower()

def download_tiktok_photos(url):
    """Скачивает ТОЛЬКО фото из карусели TikTok (строго изображения)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
        }
        
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        html = response.text
        
        photos = []
        
        # Ищем ТОЛЬКО imagePost фотографии
        pattern = r'"imagePost"[^}]*"images":\s*\[([^\]]+)\]'
        match = re.search(pattern, html)
        if match:
            images_block = match.group(1)
            url_pattern = r'"imageURL":\s*\{[^}]*"urlList":\s*\[\s*"([^"]+)"'
            matches = re.findall(url_pattern, images_block)
            for m in matches:
                clean_url = m.replace('\\u002F', '/').replace('\\/', '/')
                if clean_url.startswith('http') and clean_url not in photos:
                    photos.append(clean_url)
        
        # Fallback - более широкий поиск, но с фильтрами
        if not photos:
            pattern = r'"imageURL":\s*\{[^}]*"urlList":\s*\[\s*"([^"]+)"'
            matches = re.findall(pattern, html)
            for m in matches:
                clean_url = m.replace('\\u002F', '/').replace('\\/', '/')
                if clean_url.startswith('http') and clean_url not in photos:
                    # Строгий фильтр - исключаем обложки
                    lower_url = clean_url.lower()
                    if ('cover' not in lower_url and 
                        'thumb' not in lower_url and 
                        'origin' not in lower_url and
                        'avatar' not in lower_url and
                        'music' not in lower_url):
                        photos.append(clean_url)
        
        if not photos:
            return None
            
        downloaded = []
        seen_sizes = set()
        
        for i, photo_url in enumerate(photos[:20]):
            try:
                # Проверяем Content-Type перед скачиванием
                head_resp = requests.head(photo_url, headers=headers, timeout=10)
                content_type = head_resp.headers.get('Content-Type', '')
                
                # Пропускаем если это НЕ изображение
                if 'video' in content_type.lower():
                    continue
                if not any(t in content_type.lower() for t in ['image', 'jpeg', 'png', 'webp', 'jpg']):
                    # Если Content-Type не определён - пробуем скачать и проверить
                    pass
                
                resp = requests.get(photo_url, headers=headers, timeout=30)
                if resp.status_code == 200:
                    # Проверяем что это изображение по заголовку ответа
                    resp_content_type = resp.headers.get('Content-Type', '')
                    if 'video' in resp_content_type.lower():
                        continue
                    
                    # Проверяем размер - фото обычно 50KB-5MB
                    size = len(resp.content)
                    if size < 10000 or size > 10000000:
                        continue
                    
                    # Проверяем magic bytes - должно быть изображение
                    header_bytes = resp.content[:10]
                    is_jpeg = header_bytes[:2] == b'\xff\xd8'
                    is_png = header_bytes[:4] == b'\x89PNG'
                    is_webp = header_bytes[8:12] == b'WEBP'
                    
                    if not (is_jpeg or is_png or is_webp):
                        continue
                    
                    # Пропускаем дубликаты по размеру
                    if size in seen_sizes:
                        continue
                    seen_sizes.add(size)
                    
                    ext = 'jpg'
                    if is_png:
                        ext = 'png'
                    elif is_webp:
                        ext = 'webp'
                    
                    filename = f"tiktok_photo_{i}.{ext}"
                    with open(filename, 'wb') as f:
                        f.write(resp.content)
                    downloaded.append(filename)
                    
                    # Максимум 10 фото
                    if len(downloaded) >= 10:
                        break
            except:
                continue
        
        return downloaded if downloaded else None
    except:
        return None

def download_instagram_content(url):
    """Скачивает фото/видео/истории с Instagram"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        html = response.text
        
        photos = []
        videos = []
        
        # Ищем изображения
        img_patterns = [
            r'"display_url":\s*"([^"]+)"',
            r'"display_resources"[^]]*"src":\s*"([^"]+)"',
            r'"image_versions2"[^}]*"url":\s*"([^"]+)"',
            r'property="og:image"\s+content="([^"]+)"'
        ]
        
        for pattern in img_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                clean_url = match.replace('\\u0026', '&').replace('\\/', '/')
                if 'instagram' in clean_url or 'cdninstagram' in clean_url:
                    if clean_url not in photos:
                        photos.append(clean_url)
        
        # Ищем видео
        video_patterns = [
            r'"video_url":\s*"([^"]+)"',
            r'"contentUrl":\s*"([^"]+\.mp4[^"]*)"',
            r'property="og:video"\s+content="([^"]+)"'
        ]
        
        for pattern in video_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                clean_url = match.replace('\\u0026', '&').replace('\\/', '/')
                if clean_url not in videos:
                    videos.append(clean_url)
        
        downloaded = []
        
        # Скачиваем видео
        for i, video_url in enumerate(videos[:3]):
            try:
                resp = requests.get(video_url, headers=headers, timeout=60)
                if resp.status_code == 200:
                    filename = f"instagram_video_{i}.mp4"
                    with open(filename, 'wb') as f:
                        f.write(resp.content)
                    downloaded.append(('video', filename))
            except:
                continue
        
        # Скачиваем фото (только уникальные большие)
        seen_sizes = set()
        for i, photo_url in enumerate(photos[:10]):
            try:
                resp = requests.get(photo_url, headers=headers, timeout=30)
                if resp.status_code == 200:
                    size = len(resp.content)
                    if size > 10000 and size not in seen_sizes:
                        seen_sizes.add(size)
                        filename = f"instagram_photo_{i}.jpg"
                        with open(filename, 'wb') as f:
                            f.write(resp.content)
                        downloaded.append(('photo', filename))
            except:
                continue
        
        return downloaded if downloaded else None
    except:
        return None

def download_facebook_content(url):
    """Скачивает фото/видео/истории с Facebook"""
    try:
        cookies = get_facebook_cookies()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
        html = response.text
        
        photos = []
        videos = []
        
        # Ищем видео
        video_patterns = [
            r'"playable_url_quality_hd":\s*"([^"]+)"',
            r'"playable_url":\s*"([^"]+)"',
            r'"hd_src":\s*"([^"]+)"',
            r'"sd_src":\s*"([^"]+)"',
            r'"browser_native_hd_url":\s*"([^"]+)"',
            r'"browser_native_sd_url":\s*"([^"]+)"'
        ]
        
        for pattern in video_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                clean_url = match.replace('\\/', '/').replace('\\u0025', '%').replace('\\u0026', '&')
                if clean_url.startswith('http') and clean_url not in videos:
                    videos.append(clean_url)
        
        # Ищем фото
        photo_patterns = [
            r'"image":\s*\{[^}]*"uri":\s*"([^"]+scontent[^"]+)"',
            r'"url":\s*"(https://scontent[^"]+)"',
            r'property="og:image"\s+content="([^"]+)"',
            r'"full_image"[^}]*"uri":\s*"([^"]+)"'
        ]
        
        for pattern in photo_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                clean_url = match.replace('\\/', '/').replace('\\u0025', '%').replace('\\u0026', '&')
                if 'scontent' in clean_url and clean_url not in photos:
                    photos.append(clean_url)
        
        downloaded = []
        
        # Скачиваем видео (первое в лучшем качестве)
        for video_url in videos[:1]:
            try:
                resp = requests.get(video_url, headers=headers, cookies=cookies, timeout=120)
                if resp.status_code == 200 and len(resp.content) > 10000:
                    filename = "facebook_video_0.mp4"
                    with open(filename, 'wb') as f:
                        f.write(resp.content)
                    downloaded.append(('video', filename))
                    break
            except:
                continue
        
        # Скачиваем фото
        seen_sizes = set()
        for i, photo_url in enumerate(photos[:10]):
            try:
                resp = requests.get(photo_url, headers=headers, timeout=30)
                if resp.status_code == 200:
                    size = len(resp.content)
                    if size > 20000 and size not in seen_sizes:
                        seen_sizes.add(size)
                        filename = f"facebook_photo_{i}.jpg"
                        with open(filename, 'wb') as f:
                            f.write(resp.content)
                        downloaded.append(('photo', filename))
            except:
                continue
        
        return downloaded if downloaded else None
    except:
        return None

def download_video(url):
    """Основная функция скачивания через yt-dlp"""
    ydl_opts = {
        'format': 'best[height<=1080]/best',
        'outtmpl': 'video.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 60,
        'retries': 5,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        }
    }
    
    # Специальные настройки для YouTube
    if is_youtube_url(url):
        ydl_opts.update({
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }]
        })
    
    # Для Facebook добавляем куки
    if is_facebook_url(url) and os.path.exists(FACEBOOK_COOKIES):
        ydl_opts['cookiefile'] = FACEBOOK_COOKIES
    
    try:
        for f in os.listdir('.'):
            if f.startswith('video.'):
                os.remove(f)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        for f in os.listdir('.'):
            if f.startswith('video.'):
                return f
        return None
    except Exception as e:
        print(f"yt-dlp error: {e}")
        return None

def normalize_audio(input_path, output_path):
    """Нормализация громкости аудио"""
    try:
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
            output_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=300)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
    except:
        pass
        return input_path

def cleanup_files():
    """Удаляет временные файлы"""
    for f in os.listdir('.'):
        if any([
            f.startswith('video.'),
            f.startswith('tiktok_'),
            f.startswith('instagram_'),
            f.startswith('facebook_'),
            f.startswith('normalized_'),
            f.startswith('audio_'),
            f.startswith('slideshow_'),
            f.endswith('.mp4'),
            f.endswith('.mp3'),
            f.endswith('.jpg'),
            f.endswith('.webp'),
            f.endswith('.png'),
            f.endswith('.part')
        ]):
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
    
    if not is_valid_url(url):
        bot.reply_to(message, get_text(user_id, 'invalid_link'))
        return
    
    status_msg = bot.reply_to(message, get_text(user_id, 'downloading'))
    
    try:
        cleanup_files()
        success = False
        
        # TikTok
        if is_tiktok_url(url):
            # СНАЧАЛА пробуем видео через yt-dlp (для обычных видео и историй)
            video_path = download_video(url)
            if video_path:
                normalized = normalize_audio(video_path, 'normalized_' + video_path)
                width, height, duration = get_video_info(normalized)
                with open(normalized, 'rb') as f:
                    bot.send_video(message.chat.id, f, supports_streaming=True,
                                  width=width, height=height, duration=duration)
                
                # Извлекаем и отправляем аудио отдельно
                audio_path = extract_audio(normalized)
                if audio_path:
                    audio_duration = get_audio_duration(audio_path)
                    with open(audio_path, 'rb') as f:
                        bot.send_audio(message.chat.id, f, duration=audio_duration)
                
                success = True
            else:
                # Если видео нет - значит это фото-карусель (slideshow)
                photos = download_tiktok_photos(url)
                if photos:
                    if len(photos) == 1:
                        with open(photos[0], 'rb') as f:
                            bot.send_photo(message.chat.id, f)
                    else:
                        media = [telebot.types.InputMediaPhoto(open(p, 'rb')) for p in photos[:10]]
                        bot.send_media_group(message.chat.id, media)
                    
                    # Отправляем музыку из слайдшоу
                    audio_path = download_tiktok_audio(url)
                    if audio_path:
                        duration = get_audio_duration(audio_path)
                        with open(audio_path, 'rb') as f:
                            bot.send_audio(message.chat.id, f, duration=duration, title="TikTok Music")
                        try: os.remove(audio_path)
                        except: pass
                    
                    success = True
        
        # Instagram
        elif is_instagram_url(url):
            # Пробуем парсинг для фото/историй
            content = download_instagram_content(url)
        if content:
                videos = [c[1] for c in content if c[0] == 'video']
                photos = [c[1] for c in content if c[0] == 'photo']
                
                for video_path in videos:
                    normalized = normalize_audio(video_path, 'normalized_' + video_path)
                    width, height, duration = get_video_info(normalized)
                    with open(normalized, 'rb') as f:
                        bot.send_video(message.chat.id, f, supports_streaming=True,
                                      width=width, height=height, duration=duration)
                    success = True
                
                if photos:
                    if len(photos) == 1:
                        with open(photos[0], 'rb') as f:
                            bot.send_photo(message.chat.id, f)
                    else:
                        media = [telebot.types.InputMediaPhoto(open(p, 'rb')) for p in photos[:10]]
                        bot.send_media_group(message.chat.id, media)
                    success = True
            
            # Для Reels - yt-dlp
            if not success:
                video_path = download_video(url)
                if video_path:
                    normalized = normalize_audio(video_path, 'normalized_' + video_path)
                    width, height, duration = get_video_info(normalized)
                    with open(normalized, 'rb') as f:
                        bot.send_video(message.chat.id, f, supports_streaming=True,
                                      width=width, height=height, duration=duration)
                    success = True
        
        # Facebook
        elif is_facebook_url(url):
            # Пробуем парсинг
            content = download_facebook_content(url)
            if content:
                videos = [c[1] for c in content if c[0] == 'video']
                photos = [c[1] for c in content if c[0] == 'photo']
                
                for video_path in videos:
                    normalized = normalize_audio(video_path, 'normalized_' + video_path)
                    width, height, duration = get_video_info(normalized)
                    with open(normalized, 'rb') as f:
                        bot.send_video(message.chat.id, f, supports_streaming=True,
                                      width=width, height=height, duration=duration)
                    success = True
                
                if photos:
                    if len(photos) == 1:
                        with open(photos[0], 'rb') as f:
                            bot.send_photo(message.chat.id, f)
                    else:
                        media = [telebot.types.InputMediaPhoto(open(p, 'rb')) for p in photos[:10]]
                        bot.send_media_group(message.chat.id, media)
                    success = True
            
            # Fallback на yt-dlp
            if not success:
                video_path = download_video(url)
                if video_path:
                    normalized = normalize_audio(video_path, 'normalized_' + video_path)
                    width, height, duration = get_video_info(normalized)
                    with open(normalized, 'rb') as f:
                        bot.send_video(message.chat.id, f, supports_streaming=True,
                                      width=width, height=height, duration=duration)
                    success = True
        
        # YouTube
        elif is_youtube_url(url):
            video_path = download_video(url)
            if video_path:
                normalized = normalize_audio(video_path, 'normalized_' + video_path)
                width, height, duration = get_video_info(normalized)
                with open(normalized, 'rb') as f:
                    bot.send_video(message.chat.id, f, supports_streaming=True,
                                  width=width, height=height, duration=duration)
                success = True
        
        # Удаляем сообщение со ссылкой
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        
        if success:
            bot.edit_message_text(get_text(user_id, 'success'), message.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text(get_text(user_id, 'error'), message.chat.id, status_msg.message_id)
        
    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text(get_text(user_id, 'error'), message.chat.id, status_msg.message_id)
    finally:
        cleanup_files()

if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling()
