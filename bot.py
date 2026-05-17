import os
import subprocess
import yt_dlp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# 🔒 PROTECCIÓN PARA GITHUB: 
# No escribas tu token aquí. El servidor lo leerá automáticamente desde su configuración interna.
TOKEN = os.environ.get("TELEGRAM_TOKEN")

user_links = {}

def start(update, context):
    update.message.reply_text(
        "🔥 ¡Hola! Soy tu asistente de descargas privado en la nube.\n\n"
        "Envíame cualquier enlace de TikTok, Instagram o YouTube desde tu celular y yo me encargaré de procesarlo."
    )

def detectar_enlace(update, context):
    url = update.message.text.strip()
    chat_id = update.message.chat_id
    
    if not url.startswith("http"):
        update.message.reply_text("❌ Por favor, envía un enlace válido que empiece con http o https.")
        return

    user_links[chat_id] = url

    keyboard = [
        [InlineKeyboardButton("🎬 Descargar Video (WhatsApp Fix)", callback_data='video')],
        [InlineKeyboardButton("🎵 Descargar Audio (MP3)", callback_data='audio')],
        [InlineKeyboardButton("📸 Descargar Imágenes (Carrusel)", callback_data='imagenes')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("¿Qué formato deseas obtener para este enlace?", reply_markup=reply_markup)

def procesar_opcion(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    opcion = query.data

    url = user_links.get(chat_id)
    if not url:
        query.edit_message_text("❌ Error: El enlace expiró o no se encontró. Vuelve a enviarlo.")
        return

    query.edit_message_text("⏳ Procesando tu solicitud en el servidor... Espera un momento.")

    archivo_temp = f"temp_{chat_id}.mp4"
    archivo_final_video = f"video_{chat_id}.mp4"
    archivo_final_audio = f"audio_{chat_id}.mp3"

    # --- OPCIÓN 1: VIDEO OPTIMIZADO PARA WHATSAPP ---
    if opcion == 'video':
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': archivo_temp,
            'quiet': True
        }
        if "tiktok.com" in url:
            ydl_opts['format'] = 'nowatermark/best'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
            
            # Conversión estricta usando FFmpeg (Instalado de forma nativa en Linux/Render)
            comando = [
                'ffmpeg', '-y', '-i', archivo_temp,
                '-c:v', 'libx264', '-profile:v', 'baseline', '-level', '3.0',
                '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
                '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', archivo_final_video
            ]
            subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Devolver el archivo convertido al chat de tu celular
            context.bot.send_video(chat_id=chat_id, video=open(archivo_final_video, 'rb'), timeout=90)
            
            # Limpieza inmediata para no saturar el servidor en la nube
            if os.path.exists(archivo_temp): os.remove(archivo_temp)
            if os.path.exists(archivo_final_video): os.remove(archivo_final_video)
            
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text=f"❌ Error al procesar video: {e}")

    # --- OPCIÓN 2: AUDIO MP3 ---
    elif opcion == 'audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"audio_{chat_id}.%(ext)s",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
            
            context.bot.send_audio(chat_id=chat_id, audio=open(archivo_final_audio, 'rb'), timeout=90)
            if os.path.exists(archivo_final_audio): os.remove(archivo_final_audio)
            
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text=f"❌ Error al extraer audio: {e}")

    # --- OPCIÓN 3: IMÁGENES DE CARRUSEL ---
    elif opcion == 'imagenes':
        ydl_opts = {'extract_flat': True, 'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            entries = info.get('entries', []) or info.get('requested_downloads', [])
            contador = 0
            
            for entry in entries:
                url_foto = entry.get('url')
                if url_foto:
                    nombre_foto = f"foto_{chat_id}_{contador}.jpg"
                    # Usamos curl para descargar la imagen directamente en el servidor
                    subprocess.run(['curl', '-s', '-o', nombre_foto, url_foto])
                    context.bot.send_photo(chat_id=chat_id, photo=open(nombre_foto, 'rb'))
                    if os.path.exists(nombre_foto): os.remove(nombre_foto)
                    contador += 1
            
            if contador == 0:
                context.bot.send_message(chat_id=chat_id, text="⚠️ No se encontraron imágenes individuales en este enlace.")
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text=f"❌ Error al extraer imágenes: {e}")

    if chat_id in user_links:
        del user_links[chat_id]

def main():
    if not TOKEN:
        print("❌ ERROR CRÍTICO: No se encontró la variable TELEGRAM_TOKEN en el entorno.")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, detectar_enlace))
    dp.add_handler(CallbackQueryHandler(procesar_opcion))

    print("🚀 El bot en la nube está escuchando peticiones...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()