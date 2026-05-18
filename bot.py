import os
import yt_dlp
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ==========================================
# 🌐 CONFIGURACIÓN DEL SERVIDOR WEB (FLASK)
# ==========================================
# Render necesita un puerto web abierto (servido por gunicorn) para saber que la app está viva.
app = Flask('')

@app.route('/')
def home():
    return "Bot en línea y funcionando correctamente."

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# 📥 LÓGICA DE DESCARGA CON YT-DLP
# ==========================================
def descargar_multimedia(url, tipo):
    """
    Descarga el contenido y devuelve el nombre del archivo generado.
    tipo: 'video' o 'audio'
    """
    if tipo == 'video':
        ydl_opts = {
            'format': 'nowatermark/best/bestvideo+bestaudio',
            'outtmpl': 'video_%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'postprocessor_args': {
                'video-convertor': ['-c:v', 'libx264', '-c:a', 'aac'],
            },
            'quiet': True
        }
    else: # audio
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'audio_%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        
        # Ajustar extensión en caso de conversión a mp3
        if tipo == 'audio':
            filename = os.path.splitext(filename)[0] + '.mp3'
        elif tipo == 'video' and not filename.endswith('.mp4'):
            filename = os.path.splitext(filename)[0] + '.mp4'
            
        return filename

# ==========================================
# 🤖 COMANDOS DEL BOT DE TELEGRAM
# ==========================================
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "¡Hola! Soy tu bot descargador multimedia.\n\n"
        "Comandos disponibles:\n"
        "📹 `/video [enlace]` - Descarga en formato MP4\n"
        "🎵 `/audio [enlace]` - Descarga en formato MP3"
    )

def manejar_video(update: Update, context: CallbackContext) -> None:
    if not context.args:
        update.message.reply_text("❌ Por favor, proporciona un enlace. Ejemplo: `/video https://...`")
        return

    url = context.args[0]
    mensaje_espera = update.message.reply_text("⏳ Procesando y descargando tu video... Por favor espera.")
    
    try:
        archivo = descargar_multimedia(url, 'video')
        update.message.reply_text("🚀 ¡Descarga lista! Enviando video...")
        
        with open(archivo, 'rb') as v:
            update.message.reply_video(video=v)
            
        os.remove(archivo) # Limpiamos el almacenamiento de Render
    except Exception as e:
        update.message.reply_text(f"❌ Ocurrió un error al procesar el video: {e}")
    finally:
        mensaje_espera.delete()

def manejar_audio(update: Update, context: CallbackContext) -> None:
    if not context.args:
        update.message.reply_text("❌ Por favor, proporciona un enlace. Ejemplo: `/audio https://...`")
        return

    url = context.args[0]
    mensaje_espera = update.message.reply_text("⏳ Procesando y extrayendo el audio... Por favor espera.")
    
    try:
        archivo = descargar_multimedia(url, 'audio')
        update.message.reply_text("🚀 ¡Audio listo! Enviando...")
        
        with open(archivo, 'rb') as a:
            update.message.reply_audio(audio=a)
            
        os.remove(archivo) # Limpiamos el almacenamiento de Render
    except Exception as e:
        update.message.reply_text(f"❌ Ocurrió un error al procesar el audio: {e}")
    finally:
        mensaje_espera.delete()

# ==========================================
# 🚀 EJECUCIÓN PRINCIPAL
# ==========================================
if __name__ == '__main__':
    # TOKEN que te dio BotFather (Se recomienda usar variables de entorno)
    TOKEN = os.environ.get("TELEGRAM_TOKEN", "TU_TOKEN_AQUÍ")
    
    # 1. Iniciar servidor Flask en un hilo secundario para Render
    t = Thread(target=run_flask)
    t.start()
    
    # 2. Configurar el Bot de Telegram
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("video", manejar_video))
    dispatcher.add_handler(CommandHandler("audio", manejar_audio))

    # 3. Comenzar a escuchar mensajes de Telegram
    print("[+] Bot iniciado y escuchando comandos...")
    updater.start_polling()
    updater.idle()
