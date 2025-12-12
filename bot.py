import os
import re
import requests
import asyncio
import subprocess
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

BOT_TOKEN = os.getenv("BOT_TOKEN", "8347415373:AAG3qs04mR-CYW2zXwEf3aDvXgCUv1yNcJE")

user_languages = {}

TEXTS = {
    'ru': {
        'welcome': '👋 Привет! Отправь мне ссылку на TikTok видео или фото, и я скачаю его для тебя.',
        'select_lang': '🌍 Выберите язык:',
        'lang_set': '✅ Язык установлен: Русский',
        'error': '❌ Ошибка при скачивании',
        'send_link': '📎 Отправьте ссылку на TikTok'
    },
    'en': {
        'welcome': '👋 Hi! Send me a TikTok video or photo link and I will download it for you.',
        'select_lang': '🌍 Select language:',
        'lang_set': '✅ Language set: English',
        'error': '❌ Download error',
        'send_link': '📎 Send TikTok link'
    },
    'uk': {
        'welcome': '👋 Привіт! Надішли мені посилання на TikTok відео або фото, і я завантажу його для тебе.',
        'select_lang': '🌍 Оберіть мову:',
        'lang_set': '✅ Мову встановлено: Українська',
        'error': '❌ Помилка завантаження',
        'send_link': '📎 Надішліть посилання на TikTok'
    },
    'uz': {
        'welcome': '👋 Salom! Menga TikTok video yoki rasm havolasini yuboring, men uni siz uchun yuklab olaman.',
        'select_lang': '🌍 Tilni tanlang:',
        'lang_set': '✅ Til sozlandi: O\'zbekcha',
        'error': '❌ Yuklashda xatolik',
        'send_link': '📎 TikTok havolasini yuboring'
    },
    'kk': {
        'welcome': '👋 Сәлем! Маған TikTok видео немесе фото сілтемесін жіберіңіз, мен оны сіз үшін жүктеп аламын.',
        'select_lang': '🌍 Тілді таңдаңыз:',
        'lang_set': '✅ Тіл орнатылды: Қазақша',
        'error': '❌ Жүктеу қатесі',
        'send_link': '📎 TikTok сілтемесін жіберіңіз'
    }
}

def get_text(user_id, key):
    lang = user_languages.get(user_id, 'ru')
    return TEXTS.get(lang, TEXTS['ru']).get(key, TEXTS['ru'][key])

def get_language_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk"),
         InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kk")]
    ])

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        get_text(user_id, 'welcome'),
        reply_markup=get_language_keyboard()
    )

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang_code = query.data.replace("lang_", "")
    
    current_lang = user_languages.get(user_id)
    if current_lang == lang_code:
        await query.answer(get_text(user_id, 'lang_set'))
        return
    
    user_languages[user_id] = lang_code
    await query.answer(get_text(user_id, 'lang_set'))
    
    try:
        await query.edit_message_text(
            get_text(user_id, 'lang_set') + "\n\n" + get_text(user_id, 'welcome'),
            reply_markup=get_language_keyboard()
        )
    except Exception:
        pass

def extract_video_id(url):
    patterns = [
        r'tiktok\.com/@[\w.-]+/video/(\d+)',
        r'tiktok\.com/@[\w.-]+/photo/(\d+)',
        r'vm\.tiktok\.com/(\w+)',
        r'vt\.tiktok\.com/(\w+)',
        r'tiktok\.com/t/(\w+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def normalize_audio(input_path, output_path):
    # loudnorm нормализует громкость до стандартного уровня -14 LUFS
    cmd = ['ffmpeg', '-y', '-i', input_path, '-af', 'loudnorm=I=-14:TP=-1:LRA=11', '-c:v', 'copy', output_path]
    subprocess.run(cmd, capture_output=True)

def normalize_music_audio(input_path, output_path):
    cmd = ['ffmpeg', '-y', '-i', input_path, '-af', 'loudnorm=I=-14:TP=-1:LRA=11', output_path]
    subprocess.run(cmd, capture_output=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    url = update.message.text.strip()
    user_id = update.effective_user.id
    chat = update.effective_chat
    
    if 'tiktok.com' not in url:
        if chat.type == 'private':
            await update.message.reply_text(get_text(user_id, 'send_link'))
        return
    
    try:
        await update.message.delete()
    except:
        pass
    
    loading_msg = await chat.send_message("⏳")
    
    try:
        video_id = extract_video_id(url)
        api_url = f"https://www.tikwm.com/api/?url={url}&hd=1"
        response = requests.get(api_url, timeout=30)
        data = response.json()
        
        if data.get('code') != 0:
            await loading_msg.delete()
            await chat.send_message(get_text(user_id, 'error'))
            return
        
        video_data = data.get('data', {})
        images = video_data.get('images', [])
        music_url = video_data.get('music')
        caption = "Скачано с @tiktok27_bot"
        
        if images:
            photos = images[:50]
            local_photos = []
            
            for img_url in photos:
                try:
                    img_response = requests.get(img_url, timeout=30)
                    if img_response.status_code == 200:
                        local_photos.append(img_response.content)
                except:
                    continue
            
            await loading_msg.delete()
            
            for chunk_start in range(0, len(local_photos), 10):
                chunk = local_photos[chunk_start:chunk_start + 10]
                media = []
                for i, photo_bytes in enumerate(chunk):
                    if i == 0:
                        media.append(InputMediaPhoto(photo_bytes, caption=caption))
                    else:
                        media.append(InputMediaPhoto(photo_bytes))
                if media:
                    await chat.send_media_group(media=media)
                    await asyncio.sleep(0.5)
            
            if music_url:
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_in:
                    music_response = requests.get(music_url, timeout=30)
                    tmp_in.write(music_response.content)
                    tmp_in_path = tmp_in.name
                
                tmp_out_path = tmp_in_path.replace('.mp3', '_boosted.mp3')
                normalize_music_audio(tmp_in_path, tmp_out_path)
                
                with open(tmp_out_path, 'rb') as audio_file:
                    await chat.send_audio(audio=audio_file, caption=caption)
                
                os.unlink(tmp_in_path)
                os.unlink(tmp_out_path)
        else:
            # Приоритет: HD без водяного знака -> HD -> обычное
            video_url = video_data.get('hdplay') or video_data.get('wmplay') or video_data.get('play')
            
            if video_url:
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_in:
                    video_response = requests.get(video_url, timeout=60)
                    tmp_in.write(video_response.content)
                    tmp_in_path = tmp_in.name
                
                tmp_out_path = tmp_in_path.replace('.mp4', '_boosted.mp4')
                normalize_audio(tmp_in_path, tmp_out_path)
                
                await loading_msg.delete()
                
                with open(tmp_out_path, 'rb') as video_file:
                    await chat.send_video(video=video_file, caption=caption)
                
                os.unlink(tmp_in_path)
                os.unlink(tmp_out_path)
                
                if music_url:
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_in:
                        music_response = requests.get(music_url, timeout=30)
                        tmp_in.write(music_response.content)
                        tmp_in_path = tmp_in.name
                    
                    tmp_out_path = tmp_in_path.replace('.mp3', '_boosted.mp3')
                    normalize_music_audio(tmp_in_path, tmp_out_path)
                    
                    with open(tmp_out_path, 'rb') as audio_file:
                        await chat.send_audio(audio=audio_file, caption=caption)
                    
                    os.unlink(tmp_in_path)
                    os.unlink(tmp_out_path)
            else:
                await loading_msg.delete()
                await chat.send_message(get_text(user_id, 'error'))
    
    except Exception as e:
        try:
            await loading_msg.delete()
        except:
            pass
        await chat.send_message(f"{get_text(user_id, 'error')}: {str(e)}")

def main():
    request = HTTPXRequest(read_timeout=60, write_timeout=60, connect_timeout=30)
    application = Application.builder().token(BOT_TOKEN).request(request).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot started...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
        
