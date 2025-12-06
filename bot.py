import telebot
import yt_dlp
import os
import subprocess
import json
import re
import requests

BOT_TOKEN = "8347415373:AAE86SZs9sHvHXIiNPv5h_1tPZf6hmLYGjI"
ADMIN_ID = 6272691860

bot = telebot.TeleBot(BOT_TOKEN)

user_lang = {}

texts = {
    'ru': {
        'start': '👋 Привет! Отправь мне ссылку на видео или фото из TikTok\n\n📹 Видео и истории\n🖼 Фото-карусели',
        'downloading': '⏳ Скачиваю...',
        'success': '✅ Готово!',
        'error': '❌ Не удалось скачать. Проверь ссылку.',
        'invalid_link': '❌ Отправь корректную ссылку',
        'lang_set': '✅ Язык изменён на Русский'
    },
    'en': {
        'start': '👋 Hi! Send me a link to video or photo from TikTok\n\n📹 Videos and stories\n🖼 Photo carousels',
        'downloading': '⏳ Downloading...',
        'success': '✅ Done!',
        'error': '❌ Failed to download. Check the link.',
        'invalid_link': '❌ Send a valid link',
        'lang_set': '✅ Language changed to English'
    },
    'kz': {
        'start': '👋 Сәлем! TikTok-тан видео немесе фото сілтемесін жібер\n\n📹 Видео және stories\n🖼 Фото-карусельдер',
        'downloading': '⏳ Жүктелуде...',
        'success': '✅ Дайын!',
        'error': '❌ Жүктеу сәтсіз. Сілтемені тексер.',
        'invalid_link': '❌ Дұрыс сілтеме жібер',
        'lang_set': '✅ Тіл Қазақшаға өзгертілді'
    },
    'ua': {
        'start': '👋 Привіт! Надішли мені посилання на відео або фото з TikTok\n\n📹 Відео та історії\n🖼 Фото-каруселі',
        'downloading': '⏳ Завантажую...',
        'success': '✅ Готово!',
        'error': '❌ Не вдалося завантажити. Перевір посилання.',
        'invalid_link': '❌ Надішли коректне посилання',
        'lang_set': '✅ Мову змінено на Українську'
    },
    'uz': {
        'start': '👋 Salom! TikTok-dan video yoki rasm havolasini yubor\n\n📹 Video va stories\n🖼 Foto-karusellar',
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
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', '-show_format', video_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        width, height, duration = None, None, None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                width = stream.get('width')
                height = stream.get('height')
                break
        if 'format' in data and data['format'].get('duration'):
            duration = int(float(data['format']['duration']))
        return width, height, duration
    except:
        return None, None, None

def download_tiktok_photos(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'}
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        html = response.text
        
        photos = []
        pattern = r'"imageURL":\s*\{[^}]*"urlList":\s*\[\s*"([^"]+)"'
        matches = re.findall(pattern, html)
        for m in matches:
            clean_url = m.replace('\\u002F', '/').replace('\\/', '/')
            if clean_url.startswith('http') and clean_url not in photos:
                lower = clean_url.lower()
                if 'cover' not in lower and 'thumb' not in lower and 'avatar' not in lower:
                    photos.append(clean_url)
        
        if not photos:
            return None
        
        downloaded = []
        seen_sizes = set()
        for i, photo_url in enumerate(photos[:15]):
            try:
                resp = requests.get(photo_url, headers=headers, timeout=30)
                if resp.status_code == 200:
                    content = resp.content
                    size = len(content)
                    
                    # Проверяем magic bytes - должно быть изображение
                    is_jpeg = content[:2] == b'\xff\xd8'
                    is_png = content[:4] == b'\x89PNG'
                    is_webp = content[8:12] == b'WEBP'
                    
                    # Пропускаем если это НЕ изображение (видео/другое)
                    if not (is_jpeg or is_png or is_webp):
                        continue
                    
                    if 10000 < size < 10000000 and size not in seen_sizes:
                        seen_sizes.add(size)
                        ext = 'jpg' if is_jpeg else ('png' if is_png else 'webp')
                        filename = f"tiktok_photo_{i}.{ext}"
                        with open(filename, 'wb') as f:
                            f.write(content)
                        downloaded.append(filename)
                        
                        if len(downloaded) >= 10:
                            break
            except:
                continue
        
        return downloaded if downloaded else None
    except:
        return None
        

def cleanup_files():
    for f in os.listdir('.'):
        if f.startswith('video.') or f.startswith('tiktok_') or f.endswith('.mp4') or f.endswith('.jpg'):
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
    
    if 'tiktok.com' not in url.lower() and 'vm.tiktok.com' not in url.lower():
        bot.reply_to(message, get_text(user_id, 'invalid_link'))
        return
    
    status_msg = bot.reply_to(message, get_text(user_id, 'downloading'))
    
    try:
        cleanup_files()
        success = False
        
        # Пробуем скачать видео
        video_path = download_tiktok_video(url)
        if video_path:
            width, height, duration = get_video_info(video_path)
            with open(video_path, 'rb') as f:
                bot.send_video(message.chat.id, f, supports_streaming=True,
                              width=width, height=height, duration=duration)
            success = True
        else:
            # Если видео нет - скачиваем фото
            photos = download_tiktok_photos(url)
            if photos:
                if len(photos) == 1:
                    with open(photos[0], 'rb') as f:
                        bot.send_photo(message.chat.id, f)
                else:
                    media = [telebot.types.InputMediaPhoto(open(p, 'rb')) for p in photos[:10]]
                    bot.send_media_group(message.chat.id, media)
                success = True
        
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
    
