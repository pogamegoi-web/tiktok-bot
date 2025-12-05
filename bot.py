import telebot
from telebot import types
import yt_dlp
import os
import re
import subprocess
import glob
import json

BOT_TOKEN = "8347415373:AAE86SZs9sHvHXIiNPv5h_1tPZf6hmLYGjI"
ADMIN_ID = 6272691860

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище языков пользователей
user_languages = {}

# Тексты на разных языках
texts = {
    'ru': {
        'start': '👋 Привет! Я бот для скачивания видео.\n\n📱 Поддерживаю: TikTok, Instagram, YouTube\n\n✨ Просто отправь мне ссылку и я скачаю видео без водяного знака!',
        'choose_lang': '🌍 Выберите язык:',
        'lang_set': '✅ Язык изменён на Русский',
        'downloading': '⏳',
        'error': '❌ Не удалось скачать. Проверьте ссылку.',
        'video_caption': 'Скачано с @tiktok27_bot 🎬',
        'audio_caption': 'Скачано с @tiktok27_bot 🎵',
        'photo_caption': 'Скачано с @tiktok27_bot 📷'
    },
    'en': {
        'start': '👋 Hello! I am a video download bot.\n\n📱 Supported: TikTok, Instagram, YouTube\n\n✨ Just send me a link and I will download the video without watermark!',
        'choose_lang': '🌍 Choose language:',
        'lang_set': '✅ Language changed to English',
        'downloading': '⏳',
        'error': '❌ Failed to download. Check the link.',
        'video_caption': 'Downloaded with @tiktok27_bot 🎬',
        'audio_caption': 'Downloaded with @tiktok27_bot 🎵',
        'photo_caption': 'Downloaded with @tiktok27_bot 📷'
    },
    'kz': {
        'start': '👋 Сәлем! Мен бейне жүктеу ботымын.\n\n📱 Қолдау: TikTok, Instagram, YouTube\n\n✨ Маған сілтеме жіберіңіз, мен бейнені су белгісінсіз жүктеймін!',
        'choose_lang': '🌍 Тілді таңдаңыз:',
        'lang_set': '✅ Тіл Қазақшаға өзгертілді',
        'downloading': '⏳',
        'error': '❌ Жүктеу мүмкін болмады. Сілтемені тексеріңіз.',
        'video_caption': '@tiktok27_bot арқылы жүктелді 🎬',
        'audio_caption': '@tiktok27_bot арқылы жүктелді 🎵',
        'photo_caption': '@tiktok27_bot арқылы жүктелді 📷'
    },
    'ua': {
        'start': '👋 Привіт! Я бот для завантаження відео.\n\n📱 Підтримую: TikTok, Instagram, YouTube\n\n✨ Просто надішліть мені посилання і я завантажу відео без водяного знаку!',
        'choose_lang': '🌍 Оберіть мову:',
        'lang_set': '✅ Мову змінено на Українську',
        'downloading': '⏳',
        'error': '❌ Не вдалося завантажити. Перевірте посилання.',
        'video_caption': 'Завантажено з @tiktok27_bot 🎬',
        'audio_caption': 'Завантажено з @tiktok27_bot 🎵',
        'photo_caption': 'Завантажено з @tiktok27_bot 📷'
    },
    'uz': {
        'start': '👋 Salom! Men video yuklovchi botman.\n\n📱 Qo\'llab-quvvatlayman: TikTok, Instagram, YouTube\n\n✨ Menga havola yuboring va men videoni suv belgisisiz yuklab beraman!',
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

def get_video_info(video_path):
    """Получает метаданные видео через ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', '-show_format', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        width = 720
        height = 1280
        duration = 0
        
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

def download_video(url):
    output_path = f'video_{os.getpid()}.mp4'
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best',
        'merge_output_format': 'mp4',
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

def download_photos(url):
    """Скачивает фото с TikTok"""
    output_dir = f'photos_{os.getpid()}'
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': f'{output_dir}/photo_%(autonumber)s.%(ext)s',
        'write_thumbnail': True,
        'skip_download': False,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
            
        photos = []
        for ext in ['jpg', 'jpeg', 'png', 'webp']:
            photos.extend(glob.glob(f'{output_dir}/*.{ext}'))
        
        if photos:
            return sorted(photos)
            
    except Exception as e:
        print(f"Photo download error: {e}")
    
    return None

def download_instagram_photos(url):
    """Скачивает фото из Instagram"""
    output_dir = f'insta_photos_{os.getpid()}'
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info:
                if 'entries' in info:
                    photos = []
                    for i, entry in enumerate(info['entries']):
                        if entry.get('url') and entry.get('ext') != 'mp4':
                            img_url = entry.get('url') or entry.get('thumbnail')
                            if img_url:
                                import requests
                                response = requests.get(img_url)
                                if response.status_code == 200:
                                    photo_path = f'{output_dir}/photo_{i}.jpg'
                                    with open(photo_path, 'wb') as f:
                                        f.write(response.content)
                                    photos.append(photo_path)
                    if photos:
                        return photos
                        
                elif info.get('thumbnail') and info.get('ext') != 'mp4':
                    img_url = info.get('url') or info.get('thumbnail')
                    if img_url:
                        import requests
                        response = requests.get(img_url)
                        if response.status_code == 200:
                            photo_path = f'{output_dir}/photo_0.jpg'
                            with open(photo_path, 'wb') as f:
                                f.write(response.content)
                            return [photo_path]
                            
    except Exception as e:
        print(f"Instagram photo download error: {e}")
    
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
                # Получаем метаданные для автовоспроизведения
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
            
            if is_instagram_url(url):
                photos = download_instagram_photos(url)
            elif is_tiktok_url(url):
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
            
