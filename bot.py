import os
import re
import asyncio
import requests
import subprocess
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8347415373:AAE86SZs9sHvHXIiNPv5h_1tPZf6hmLYGjI')

# GIF песочных часов
LOADING_GIF = "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif"

user_languages = {}

TEXTS = {
    'ru': {
        'welcome': "🎬 Video Downloader Bot\n\nПривет! Я могу скачать видео из:\n• TikTok\n\n✨ Без водяного знака и в HD!\n\nКак использовать:\nПросто отправь мне ссылку на видео!",
        'lang_set': "✅ Язык изменён на Русский",
        'error': "❌ Ошибка",
        'caption': "Скачано с @tiktok27_bot"
    },
    'en': {
        'welcome': "🎬 Video Downloader Bot\n\nHello! I can download videos from:\n• TikTok\n\n✨ No watermark and in HD!\n\nHow to use:\nJust send me a video link!",
        'lang_set': "✅ Language changed to English",
        'error': "❌ Error",
        'caption': "Downloaded via @tiktok27_bot"
    },
    'uk': {
        'welcome': "🎬 Video Downloader Bot\n\nПривіт! Я можу завантажити відео з:\n• TikTok\n\n✨ Без водяного знаку та в HD!\n\nЯк використовувати:\nПросто надішли мені посилання на відео!",
        'lang_set': "✅ Мову змінено на Українську",
        'error': "❌ Помилка",
        'caption': "Завантажено з @tiktok27_bot"
    },
    'uz': {
        'welcome': "🎬 Video Downloader Bot\n\nSalom! Men quyidagi videolarni yuklab olishim mumkin:\n• TikTok\n\n✨ Suv belgisisiz va HD sifatda!\n\nQanday foydalanish:\nMenga video havolasini yuboring!",
        'lang_set': "✅ Til O'zbek tiliga o'zgartirildi",
        'error': "❌ Xato",
        'caption': "@tiktok27_bot orqali yuklandi"
    },
    'kk': {
        'welcome': "🎬 Video Downloader Bot\n\nСәлем! Мен видео жүктей аламын:\n• TikTok\n\n✨ Су белгісіз және HD сапада!\n\nҚалай пайдалану:\nМаған видео сілтемесін жіберіңіз!",
        'lang_set': "✅ Тіл Қазақшаға өзгертілді",
        'error': "❌ Қате",
        'caption': "@tiktok27_bot арқылы жүктелді"
    }
}

def get_text(user_id, key):
    lang = user_languages.get(user_id, 'ru')
    return TEXTS.get(lang, TEXTS['ru']).get(key, TEXTS['ru'][key])

def get_lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
         InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz")],
        [InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kk")]
    ])

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(get_text(user_id, 'welcome'), reply_markup=get_lang_keyboard())

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang_code = query.data.replace("lang_", "")
    user_languages[user_id] = lang_code
    await query.edit_message_text(get_text(user_id, 'welcome'), reply_markup=get_lang_keyboard())
    await query.message.reply_text(get_text(user_id, 'lang_set'))

def extract_video_id(url):
    try:
        if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url:
            response = requests.head(url, allow_redirects=True, timeout=10)
            url = response.url
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        match = re.search(r'/photo/(\d+)', url)
        if match:
            return match.group(1)
    except:
        pass
    return None

def boost_audio(input_path, output_path):
    cmd = ['ffmpeg', '-y', '-i', input_path, '-af', 'volume=2.3', '-c:v', 'copy', output_path]
    subprocess.run(cmd, capture_output=True)

def boost_music_audio(input_path, output_path):
    cmd = ['ffmpeg', '-y', '-i', input_path, '-af', 'volume=1.7', output_path]
    subprocess.run(cmd, capture_output=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    chat = update.message.chat
    
    if 'tiktok.com' not in text:
        return
    
    try:
        await update.message.delete()
    except:
        pass
    
    # Отправляем GIF загрузки
    loading_msg = await chat.send_animation(LOADING_GIF)
    
    try:
        video_id = extract_video_id(text)
        if not video_id:
            await loading_msg.delete()
            await chat.send_message(get_text(user_id, 'error'))
            return
        
        api_url = f"https://tikwm.com/api/?url=https://www.tiktok.com/@user/video/{video_id}"
        response = requests.get(api_url, timeout=15)
        data = response.json()
        
        if data.get('code') != 0:
            await loading_msg.delete()
            await chat.send_message(get_text(user_id, 'error'))
            return
        
        video_data = data.get('data', {})
        photos = video_data.get('images', [])
        caption = get_text(user_id, 'caption')
        music_url = video_data.get('music')
        
        await loading_msg.delete()
        
        if photos:
            photos = photos[:30]
            local_photos = []
            for i, photo_url in enumerate(photos):
                try:
                    resp = requests.get(photo_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                    if resp.status_code == 200:
                        filename = f'photo_{i}.jpg'
                        with open(filename, 'wb') as f:
                            f.write(resp.content)
                        local_photos.append(filename)
                except:
                    continue
            
            if local_photos:
                for chunk_start in range(0, len(local_photos), 10):
                    chunk = local_photos[chunk_start:chunk_start + 10]
                    media = []
                    for i, filename in enumerate(chunk):
                        with open(filename, 'rb') as f:
                            photo_bytes = f.read()
                        if i == 0:
                            media.append(InputMediaPhoto(photo_bytes, caption=caption))
                        else:
                            media.append(InputMediaPhoto(photo_bytes))
                    if media:
                        await chat.send_media_group(media)
                for filename in local_photos:
                    try:
                        os.remove(filename)
                    except:
                        pass
            
            if music_url:
                music_resp = requests.get(music_url, timeout=30)
                if music_resp.status_code == 200:
                    with open('music.mp3', 'wb') as f:
                        f.write(music_resp.content)
                    boost_music_audio('music.mp3', 'music_boosted.mp3')
                    if os.path.exists('music_boosted.mp3'):
                        await chat.send_audio(open('music_boosted.mp3', 'rb'), caption=caption)
                        os.remove('music_boosted.mp3')
                    if os.path.exists('music.mp3'):
                        os.remove('music.mp3')
        else:
            video_url = video_data.get('hdplay') or video_data.get('play')
            if video_url:
                video_resp = requests.get(video_url, timeout=60)
                if video_resp.status_code == 200:
                    with open('video.mp4', 'wb') as f:
                        f.write(video_resp.content)
                    boost_audio('video.mp4', 'video_boosted.mp4')
                    
                    if os.path.exists('video_boosted.mp4'):
                        await chat.send_video(open('video_boosted.mp4', 'rb'), caption=caption)
                        os.remove('video_boosted.mp4')
                    else:
                        await chat.send_video(open('video.mp4', 'rb'), caption=caption)
                    if os.path.exists('video.mp4'):
                        os.remove('video.mp4')
                    
                    if music_url:
                        music_resp = requests.get(music_url, timeout=30)
                        if music_resp.status_code == 200:
                            with open('music.mp3', 'wb') as f:
                                f.write(music_resp.content)
                            boost_music_audio('music.mp3', 'music_boosted.mp3')
                            if os.path.exists('music_boosted.mp3'):
                                await chat.send_audio(open('music_boosted.mp3', 'rb'), caption=caption)
                                os.remove('music_boosted.mp3')
                            if os.path.exists('music.mp3'):
                                os.remove('music.mp3')
    except Exception as e:
        try:
            await loading_msg.delete()
        except:
            pass
        await chat.send_message(f"{get_text(user_id, 'error')}: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
