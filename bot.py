import os
import yt_dlp

def descargar_video(url):
    print("\n[+] Configurando descarga de video (Formato MP4 compatible)...")
    ydl_opts = {
        # 'nowatermark/best' intenta evadir la marca de agua nativa en plataformas como TikTok
        'format': 'nowatermark/best/bestvideo+bestaudio',
        'outtmpl': 'video_%(title)s.%(ext)s',
        # Forzamos la conversión con FFmpeg a un formato H.264/AAC nativo para WhatsApp
        'merge_output_format': 'mp4',
        'postprocessor_args': {
            'video-convertor': ['-c:v', 'libx264', '-c:a', 'aac'],
        },
        'quiet': False
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("[+] ¡Video descargado y convertido con éxito para móviles!")
    except Exception as e:
        print(f"[-] Error al descargar el video: {e}")

def descargar_audio(url):
    print("\n[+] Configurando descarga de audio (Formato MP3)...")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio_%(title)s.%(ext)s',
        # Extraemos el audio puro usando FFmpeg
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("[+] ¡Audio MP3 descargado con éxito!")
    except Exception as e:
        print(f"[-] Error al descargar el audio: {e}")

def menu():
    while True:
        print("\n=======================================")
        print("    DESCARGADOR MULTIMEDIA (SIN MARCA) ")
        print("=======================================")
        print("1. Descargar Video (MP4 para WhatsApp)")
        print("2. Descargar Audio (MP3)")
        print("3. Salir")
        print("=======================================")
        
        opcion = input("Selecciona una opción (1-3): ").strip()
        
        if opcion == "3":
            print("[+] Saliendo del descargador. ¡Hasta luego!")
            break
            
        if opcion in ["1", "2"]:
            enlace = input("\nPegue el enlace del video aquí: ").strip()
            if not enlace:
                print("[-] El enlace no puede estar vacío.")
                continue
                
            if opcion == "1":
                descargar_video(enlace)
            elif opcion == "2":
                descargar_audio(enlace)
        else:
            print("[-] Opción no válida. Por favor, selecciona 1, 2 o 3.")

if __name__ == "__main__":
    menu()
