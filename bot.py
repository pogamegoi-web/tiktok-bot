import telebot
from telebot import types
import yt_dlp
import os
import re
import subprocess
import glob
import json
import requests

BOT_TOKEN = "8347415373:AAE86SZs9sHvHXIiNPv5h_1tPZf6hmLYGjI"
ADMIN_ID = 6272691860

# Путь к файлу cookies Facebook
FACEBOOK_COOKIES = "facebook_cookies.txt"

bot = telebot.TeleBot(BOT_TOKEN)

user_languages = {}

texts = {
    'ru': {
        'start': '👋 Привет! Я бот для скачивания видео и фото.\n\n📱 Поддерживаю:\n• TikTok\n• Instagram\n• YouTube\n• Pinterest\n• Facebook\n• Likee\n\n✨ Просто отправь мне ссылку!',
        'choose_lang': '🌍 Выберите язык:',
        'lang_set': '✅ Язык изменён на Русский',
        'downloading': '⏳',
        'error': '❌ Не удалось скачать. Проверьте ссылку.',
        'video_caption': 'Скачано с @tiktok27_bot 🎬',
        'audio_caption': 'Скачано с @tiktok27_bot 🎵',
        'photo_caption': 'Скачано с @tiktok27_bot 📷'
    },
    'en': {
        'start': '👋 Hello! I download videos and photos.\n\n📱 Supported:\n• TikTok\n• Instagram\n• YouTube\n• Pinterest\n• Facebook\n• Likee\n\n✨ Just send me a link!',
        'choose_lang': '🌍 Choose language:',
        'lang_set': '✅ Language changed to English',
        'downloading': '⏳',
        'error': '❌ Failed to download. Check the link.',
        'video_caption': 'Downloaded with @tiktok27_bot 🎬',
        'audio_caption': 'Downloaded with @tiktok27_bot 🎵',
        'photo_caption': 'Downloaded with @tiktok27_bot 📷'
    },
    'kz': {
        'start': '👋 Сәлем! Мен бейне мен фото жүктеймін.\n\n📱 Қолдау:\n• TikTok\n• Instagram\n• YouTube\n• Pinterest\n• Facebook\n• Likee\n\n✨ Маған сілтеме жіберіңіз!',
        'choose_lang': '🌍 Тілді таңдаңыз:',
        'lang_set': '✅ Тіл Қазақшаға өзгертілді',
        'downloading': '⏳',
        'error': '❌ Жүктеу мүмкін болмады. Сілтемені тексеріңіз.',
        'video_caption': '@tiktok27_bot арқылы жүктелді 🎬',
        'audio_caption': '@tiktok27_bot арқылы жүктелді 🎵',
        'photo_caption': '@tiktok27_bot арқылы жүктелді 📷'
    },
    'ua': {
        'start': '👋 Привіт! Я завантажую відео та фото.\n\n📱 Підтримую:\n• TikTok\n• Instagram\n• YouTube\n• Pinterest\n• Facebook\n• Likee\n\n✨ Просто надішліть мені посилання!',
        'choose_lang': '🌍 Оберіть мову:',
        'lang_set': '✅ Мову змінено на Українську',
        'downloading': '⏳',
        'error': '❌ Не вдалося завантажити. Перевірте посилання.',
        'video_caption': 'Завантажено з @tiktok27_bot 🎬',
        'audio_caption': 'Завантажено з @tiktok27_bot 🎵',
        'photo_caption': 'Завантажено з @tiktok27_bot 📷'
    },
    'uz': {
        'start': '👋 Salom! Men video va foto yuklayman.\n\n📱 Qo\'llab-quvvatlayman:\n• TikTok\n• Instagram\n• YouTube\n• Pinterest\n• Facebook\n• Likee\n\n✨ Menga havola yuboring!',
        'choose_lang': '🌍 Tilni tanlang:',
        'lang_set': '✅ Til O\'zbekchaga o\'zgartirildi',
        'downloading': '⏳',
        'error': '❌ Yuklab bo\'lmadi. Havolani tekshiring.',
        'video_caption': '@tiktok27_bot orqali yuklandi 🎬',
        'audio_caption': '@tiktok27_bot orqali yuklandi 🎵',
        'photo_caption': '@tiktok27_bot orqali yuklandi 📷'
    }
}

def get_text(user_id, key):
    lang = user_languages.get(user_id, 'ru')
    return texts[lang][key]

def is_instagram_url(url):
    return 'instagram.com' in url or 'instagr.am' in url

def is_tiktok_url(url):
    return 'tiktok.com' in url or 'vm.tiktok.com' in url

def is_facebook_url(url):
    return 'facebook.com' in url or 'fb.watch' in url or 'fb.com' in url

def is_likee_url(url):
    return 'likee.video' in url or 'l.likee.video' in url or 'likee.com' in url

def is_pinterest_url(url):
    return 'pinterest.com' in url or 'pin.it' in url

def is_photo_platform(url):
    return is_instagram_url(url) or is_tiktok_url(url) or is_pinterest_url(url)

def get_video_info(video_path):
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', '-show_format', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        width, height, duration = 720, 1280, 0
        
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                width = stream.get('width', 720)
                height = stream.get('height', 1280)
                break
        
        if 'format' in data:
            duration = int(float(data['format'].get('duration', 0)))
        
        return width, height, duration
    except:
        return 720, 1280, 0

def download_likee_video(url):
    """Специальный загрузчик для Likee"""
    output_path = f'video_{os.getpid()}.mp4'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://likee.video/',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        html = response.text
        
        patterns = [
            r'"video_url"\s*:\s*"([^"]+)"',
            r'"playUrl"\s*:\s*"([^"]+)"',
            r'source\s+src="([^"]+\.mp4[^"]*)"',
            r'"videoUrl"\s*:\s*"([^"]+)"',
        ]
        
        video_url = None
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                video_url = match.group(1).replace('\\u002F', '/').replace('\\/', '/')
                break
        
        if video_url:
            video_response = requests.get(video_url, headers=headers, timeout=60)
            if video_response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(video_response.content)
                return output_path
                
    except Exception as e:
        print(f"Likee download error: {e}")
    
    return None

def download_facebook_video(url):
    """Загрузчик для Facebook с cookies"""
    output_path = f'video_{os.getpid()}.mp4'
    
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        'socket_timeout': 30,
    }
    
    # Добавляем cookies если файл существует
    if os.path.exists(FACEBOOK_COOKIES):
        ydl_opts['cookiefile'] = FACEBOOK_COOKIES
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if os.path.exists(output_path):
            return output_path
    except Exception as e:
        print(f"Facebook download error: {e}")
    
    return None

def download_video(url):
    output_path = f'video_{os.getpid()}.mp4'
    
    # Специальные загрузчики
    if is_likee_url(url):
        result = download_likee_video(url)
        if result:
            return result
    
    if is_facebook_url(url):
        result = download_facebook_video(url)
        if result:
            return result
    
    # Стандартный yt-dlp
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best',
        'merge_output_format': 'mp4',
        'postprocessor_args': {
            'ffmpeg': ['-af', 'loudnorm=I=-16:TP=-1.5:LRA=11']
        },
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        'socket_timeout': 30,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if os.path.exists(output_path):
            return output_path
    except Exception as e:
        print(f"Video download error: {e}")
    return None

def download_audio(url):
    output_path = f'audio_{os.getpid()}.mp3'
    ydl_opts = {
        'outtmpl': output_path.replace('.mp3', '.%(ext)s'),
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '0',
        }],
        'postprocessor_args': {
            'ffmpeg': ['-af', 'loudnorm=I=-16:TP=-1.5:LRA=11']
        },
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if os.path.exists(output_path):
            return output_path
    except Exception as e:
        print(f"Audio download error: {e}")
    return None

def download_pinterest_image(url):
    output_dir = f'pinterest_{os.getpid()}'
    os.makedirs(output_dir, exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        html = response.text
        
        patterns = [
            r'"originals":\s*{\s*"url":\s*"([^"]+)"',
            r'<meta property="og:image" content="([^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                img_url = match.group(1).replace('\\u002F', '/')
                img_response = requests.get(img_url, headers=headers, timeout=30)
                if img_response.status_code == 200:
                    photo_path = f'{output_dir}/pinterest.jpg'
                    with open(photo_path, 'wb') as f:
                        f.write(img_response.content)
                    return [photo_path]
                    
    except Exception as e:
        print(f"Pinterest download error: {e}")
    
    return None

def download_photos(url):
    if is_pinterest_url(url):
        return download_pinterest_image(url)
    
    output_dir = f'photos_{os.getpid()}'
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        ydl_opts = {
            'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return None
                
            photos = []
            
            if 'entries' in info:
                for i, entry in enumerate(info['entries']):
                    if entry.get('ext') == 'mp4' or entry.get('vcodec') not in [None, 'none']:
                        continue
                    img_url = entry.get('url') or entry.get('thumbnail')
                    if img_url:
                        try:
                            response = requests.get(img_url, timeout=30)
                            if response.status_code == 200:
                                photo_path = f'{output_dir}/photo_{i}.jpg'
                                with open(photo_path, 'wb') as f:
                                    f.write(response.content)
                                photos.append(photo_path)
                        except:
                            pass
            else:
                img_url = info.get('url') or info.get('thumbnail')
                if img_url and info.get('ext') != 'mp4':
                    try:
                        response = requests.get(img_url, timeout=30)
                        if response.status_code == 200:
                            photo_path = f'{output_dir}/photo_0.jpg'
                            with open(photo_path, 'wb') as f:
                                f.write(response.content)
                            photos.append(photo_path)
                    except:
                        pass
            
            if not photos:
                for ext in ['jpg', 'jpeg', 'png', 'webp']:
                    photos.extend(glob.glob(f'{output_dir}/*.{ext}'))
            
            if photos:
                return sorted(photos)
                
    except Exception as e:
        print(f"Photo download error: {e}")
    
    return None

def cleanup_photos(photos):
    if photos:
        for photo in photos:
            try:
                os.remove(photo)
            except:
                pass
        try:
            dir_path = os.path.dirname(photos[0])
            if dir_path and os.path.exists(dir_path):
                os.rmdir(dir_path)
        except:
            pass

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, get_text(message.from_user.id, 'start'))

@bot.message_handler(commands=['language'])
def language_command(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        types.InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kz"),
        types.InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua"),
        types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")
    )
    bot.send_message(message.chat.id, get_text(message.from_user.id, 'choose_lang'), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def callback_language(call):
    lang = call.data.split('_')[1]
    user_languages[call.from_user.id] = lang
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        get_text(call.from_user.id, 'lang_set'),
        call.message.chat.id,
        call.message.message_id
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, message.text)
    
    if urls:
        url = urls[0]
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        
        loading_msg = bot.send_message(chat_id, get_text(user_id, 'downloading'))
        
        video_path = download_video(url)
        
        if video_path:
            try:
                width, height, duration = get_video_info(video_path)
                
                with open(video_path, 'rb') as video:
                    bot.send_video(
                        chat_id, 
                        video, 
                        caption=get_text(user_id, 'video_caption'),
                        supports_streaming=True,
                        width=width,
                        height=height,
                        duration=duration
                    )
                
                audio_path = download_audio(url)
                if audio_path:
                    with open(audio_path, 'rb') as audio:
                        bot.send_audio(chat_id, audio, caption=get_text(user_id, 'audio_caption'))
                    os.remove(audio_path)
                    
            except Exception as e:
                print(f"Send error: {e}")
                bot.send_message(chat_id, get_text(user_id, 'error'))
            finally:
                os.remove(video_path)
        else:
            photos = None
            if is_photo_platform(url):
                photos = download_photos(url)
            
            if photos:
                try:
                    if len(photos) == 1:
                        with open(photos[0], 'rb') as photo:
                            bot.send_photo(chat_id, photo, caption=get_text(user_id, 'photo_caption'))
                    else:
                        media_group = []
                        for i, photo_path in enumerate(photos[:10]):
                            with open(photo_path, 'rb') as f:
                                photo_data = f.read()
                            if i == 0:
                                media_group.append(types.InputMediaPhoto(photo_data, caption=get_text(user_id, 'photo_caption')))
                            else:
                                media_group.append(types.InputMediaPhoto(photo_data))
                        bot.send_media_group(chat_id, media_group)
                except Exception as e:
                    print(f"Photo send error: {e}")
                    bot.send_message(chat_id, get_text(user_id, 'error'))
                finally:
                    cleanup_photos(photos)
            else:
                bot.send_message(chat_id, get_text(user_id, 'error'))
        
        try:
            bot.delete_message(chat_id, loading_msg.message_id)
        except:
            pass

if __name__ == '__main__':
    print("Bot started...")
    bot.infinity_polling()
    
