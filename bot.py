import telebot
import yt_dlp
import os
import requests

BOT_TOKEN = "8347415373:AAE86SZs9sHvHXIiNPv5h_1tPZf6hmLYGjI"
bot = telebot.TeleBot(BOT_TOKEN)

user_lang = {}

texts = {
    'ru': {
        'start': '👋 Привет! Отправь мне ссылку из TikTok\n\n📹 Видео и фото в HD качестве\n🎵 Музыка отправляется отдельно',
        'downloading': '⏳ Скачиваю в HD...',
        'success': '✅ Готово!',
        'error': '❌ Не удалось скачать',
        'lang_set': '✅ Русский'
    },
    'en': {
        'start': '👋 Hi! Send me a TikTok link\n\n📹 Videos and photos in HD quality\n🎵 Music sent separately',
        'downloading': '⏳ Downloading in HD...',
        'success': '✅ Done!',
        'error': '❌ Failed to download',
        'lang_set': '✅ English'
    },
    'kz': {
        'start': '👋 Сәлем! TikTok сілтемесін жібер\n\n📹 Видео мен фото HD сапада\n🎵 Музыка бөлек жіберіледі',
        'downloading': '⏳ HD жүктелуде...',
        'success': '✅ Дайын!',
        'error': '❌ Жүктеу сәтсіз',
        'lang_set': '✅ Қазақша'
    },
    'ua': {
        'start': '👋 Привіт! Надішли посилання з TikTok\n\n📹 Відео та фото в HD якості\n🎵 Музика надсилається окремо',
        'downloading': '⏳ Завантажую в HD...',
        'success': '✅ Готово!',
        'error': '❌ Не вдалося завантажити',
        'lang_set': '✅ Українська'
    },
    'uz': {
        'start': '👋 Salom! TikTok havolasini yubor\n\n📹 Video va rasmlar HD sifatda\n🎵 Musiqa alohida yuboriladi',
        'downloading': '⏳ HD yuklanmoqda...',
        'success': '✅ Tayyor!',
        'error': '❌ Yuklab bo\'lmadi',
        'lang_set': '✅ O\'zbek'
    }
}

def get_text(user_id, key):
    return texts[user_lang.get(user_id, 'ru')][key]

def download_via_tikwm(url, hd=True):
    try:
        # hd=1 для HD качества
        api_url = f"https://www.tikwm.com/api/?url={url}&hd=1"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(api_url, headers=headers, timeout=30)
        data = resp.json()
        
        if data.get('code') == 0:
            d = data.get('data', {})
            return {
                'images': d.get('images', []),
                'music': d.get('music'),
                'hdplay': d.get('hdplay'),  # HD видео
                'play': d.get('play'),       # обычное видео
                'duration': d.get('duration', 0)
            }
    except:
        pass
    return None

def download_video_hd(url):
    try:
        for f in os.listdir('.'):
            if f.startswith('video.'):
                os.remove(f)
        
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            'outtmpl': 'video.%(ext)s',
            'quiet': True,
            'merge_output_format': 'mp4'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        for f in os.listdir('.'):
            if f.startswith('video.'):
                return f
    except:
        pass
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
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        success = False
        tikwm = download_via_tikwm(url)
        
        if tikwm:
            # Фото/карусель/история
            if tikwm['images']:
                downloaded = []
                for i, img_url in enumerate(tikwm['images'][:10]):
                    try:
                        resp = requests.get(img_url, headers=headers, timeout=30)
                        if resp.status_code == 200 and len(resp.content) > 5000:
                            filename = f"photo_{i}.jpg"
                            with open(filename, 'wb') as f:
                                f.write(resp.content)
                            downloaded.append(filename)
                    except:
                        continue
                
                if downloaded:
                    if len(downloaded) == 1:
                        with open(downloaded[0], 'rb') as f:
                            bot.send_photo(message.chat.id, f)
                    else:
                        media = [telebot.types.InputMediaPhoto(open(p, 'rb')) for p in downloaded]
                        bot.send_media_group(message.chat.id, media)
                    success = True
            
            # Видео - сначала HD, потом обычное
            else:
                video_url = tikwm.get('hdplay') or tikwm.get('play')
                if video_url:
                    try:
                        resp = requests.get(video_url, headers=headers, timeout=120)
                        if resp.status_code == 200 and len(resp.content) > 10000:
                            with open('video.mp4', 'wb') as f:
                                f.write(resp.content)
                            with open('video.mp4', 'rb') as f:
                                bot.send_video(message.chat.id, f)
                            success = True
                    except:
                        pass
                
                # Fallback на yt-dlp HD
                if not success:
                    video = download_video_hd(url)
                    if video:
                        with open(video, 'rb') as f:
                            bot.send_video(message.chat.id, f)
                        success = True
            
            # Музыка
            if tikwm['music']:
                try:
                    resp = requests.get(tikwm['music'], headers=headers, timeout=30)
                    if resp.status_code == 200 and len(resp.content) > 5000:
                        with open('audio.mp3', 'wb') as f:
                            f.write(resp.content)
                        with open('audio.mp3', 'rb') as f:
                            bot.send_audio(message.chat.id, f, title="TikTok Audio")
                except:
                    pass
        
        # Fallback
        if not success:
            video = download_video_hd(url)
            if video:
                with open(video, 'rb') as f:
                    bot.send_video(message.chat.id, f)
                success = True
        
        if success:
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
                                           
