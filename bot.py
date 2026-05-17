import os
import subprocess
import threading
import yt_dlp
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# --- PARTE 1: ENGAÑO PARA EL SERVIDOR GRATUITO (FLASK) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot en línea y funcionando gratis 🚀"

def iniciar_servidor_web():
    # Render asigna un puerto automático, si no, usa el 10000
    puerto = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=puerto)

# --- PARTE 2: TU BOT DE TELEGRAM ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
user_links = {}

def start(update, context):
    update.message.reply_text(
        "🔥 ¡Hola! Asistente de descargas gratuito activado.\n\n"
        "Envíame un enlace de TikTok, Instagram o YouTube."
    )

def detectar_enlace(update, context):
    url = update.message.text.strip()
    chat_id = update.message.chat_id
    
    if not url.startswith("http"):
        update.message.reply_text("❌ Envía un enlace válido.")
        return

    user_links[chat_id] = url
    keyboard = [
        [InlineKeyboardButton("🎬 Video (WhatsApp Fix)", callback_data='video')],
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data='audio')],
        [InlineKeyboardButton("📸 Imágenes (Carrusel)", callback_data='imagenes')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("¿Qué formato deseas?", reply_markup=reply_markup)

def procesar_opcion(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    opcion = query.data
    url = user_links.get(chat_id)

    if not url:
        query.edit_message_text("❌ El enlace expiró.")
        return

    query.edit_message_text("⏳ Procesando en la nube gratis...")

    archivo_temp = f"temp_{chat_id}.mp4"
    archivo_final_video = f"video_{chat_id}.mp4"
    archivo_final_audio = f"audio_{chat_id}.mp3"

    if opcion == 'video':
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': archivo_temp, 'quiet': True
        }
        if "tiktok.com" in url:
            ydl_opts['format'] = 'nowatermark/best'
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
            comando = [
                'ffmpeg', '-y', '-i', archivo_temp,
                '-c:v', 'libx264', '-profile:v', 'baseline', '-level', '3.0',
                '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
                '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', archivo_final_video
            ]
            subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            context.bot.send_video(chat_id=chat_id, video=open(archivo_final_video, 'rb'), timeout=90)
            if os.path.exists(archivo_temp): os.remove(archivo_temp)
            if os.path.exists(archivo_final_video): os.remove(archivo_final_video)
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {e}")

    elif opcion == 'audio':
        ydl_opts = {
            'format': 'bestaudio/best', 'outtmpl': f"audio_{chat_id}.%(ext)s",
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
            context.bot.send_audio(chat_id=chat_id, audio=open(archivo_final_audio, 'rb'), timeout=90)
            if os.path.exists(archivo_final_audio): os.remove(archivo_final_audio)
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {e}")

    elif opcion == 'imagenes':
        ydl_opts = {'extract_flat': True, 'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            entries = info.get('entries', []) or info.get('requested_downloads', [])
            for entry in entries:
                url_foto = entry.get('url')
                if url_foto:
                    nombre_foto = f"foto_{chat_id}.jpg"
                    subprocess.run(['curl', '-s', '-o', nombre_foto, url_foto])
                    context.bot.send_photo(chat_id=chat_id, photo=open(nombre_foto, 'rb'))
                    if os.path.exists(nombre_foto): os.remove(nombre_foto)
            if not entries:
                context.bot.send_message(chat_id=chat_id, text="⚠️ No encontré fotos.")
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {e}")

    if chat_id in user_links:
        del user_links[chat_id]

# --- PARTE 3: ARRANQUE SIMULTÁNEO ---
def main():
    if not TOKEN:
        print("❌ Falta la variable TELEGRAM_TOKEN")
        return

    # Iniciamos la web en un hilo secundario para que Render no nos corte el servicio
    t = threading.Thread(target=iniciar_servidor_web)
    t.daemon = True
    t.start()

    # Arrancamos el bot de Telegram en el hilo principal
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, detectar_enlace))
    dp.add_handler(CallbackQueryHandler(procesar_opcion))

    print("🚀 Bot Gratuito activado...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
