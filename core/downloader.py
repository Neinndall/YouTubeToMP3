import os
import sys
import re
import yt_dlp

# Aseguramos que el directorio de herramientas 'tools' esté en el PATH
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
TOOLS_DIR = os.path.join(PROJECT_DIR, "tools")

if os.path.exists(TOOLS_DIR) and TOOLS_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = TOOLS_DIR + os.pathsep + os.environ.get("PATH", "")

def sanitize_filename(name: str) -> str:
    """Elimina o reemplaza caracteres no válidos para el sistema de archivos de Windows."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = clean.strip()
    return clean if clean else "cancion"

def format_seconds(seconds: float) -> str:
    """Convierte segundos a formato MM:SS o HH:MM:SS."""
    if not seconds:
        return "00:00"
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def get_video_info(url: str) -> dict:
    """Obtiene metadatos del vídeo sin descargarlo."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'remote_components': ['ejs:github'],
        'js_runtimes': {'node': {}},
        'ffmpeg_location': TOOLS_DIR,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return {"success": False, "error": "No se pudo extraer la información del enlace."}
            
            # En caso de lista de reproducción, tomar el primer elemento para previsualización
            if 'entries' in info and info['entries']:
                entry = info['entries'][0]
                is_playlist = True
                title = info.get('title', 'Lista de reproducción')
                count = len(info['entries'])
            else:
                entry = info
                is_playlist = False
                title = entry.get('title', 'Desconocido')
                count = 1

            duration = entry.get('duration', 0)
            uploader = entry.get('uploader') or entry.get('channel') or entry.get('artist') or 'Artista desconocido'
            thumbnail = entry.get('thumbnail')
            
            return {
                "success": True,
                "title": title,
                "uploader": uploader,
                "duration": duration,
                "duration_str": format_seconds(duration),
                "thumbnail": thumbnail,
                "is_playlist": is_playlist,
                "item_count": count
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def download_audio(url: str, output_folder: str, quality: str = "320", progress_callback=None) -> dict:
    """
    Descarga el audio de YouTube en formato MP3 con metadatos y carátula incrustada.
    quality: "320", "256", "192" o "128"
    progress_callback: función que recibe un dict con datos de progreso:
       { 'status': 'downloading'|'converting'|'finished', 'percent': float, 'speed': str, 'eta': str, 'title': str }
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    downloaded_files = []
    current_title = [""]

    def ytdl_hook(d):
        status = d.get('status')
        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0
            percent = (downloaded / total * 100.0) if total > 0 else 0.0
            
            speed = d.get('speed')
            speed_str = f"{speed / (1024 * 1024):.1f} MB/s" if speed else "Calculando..."
            
            eta = d.get('eta')
            eta_str = f"{eta}s" if eta else "--"

            filename = d.get('filename', '')
            base = os.path.basename(filename)
            if base:
                current_title[0] = os.path.splitext(base)[0]

            if progress_callback:
                progress_callback({
                    'status': 'downloading',
                    'percent': min(percent, 99.0),
                    'speed': speed_str,
                    'eta': eta_str,
                    'title': current_title[0]
                })

        elif status == 'finished':
            filename = d.get('filename')
            if filename:
                downloaded_files.append(filename)
            if progress_callback:
                progress_callback({
                    'status': 'converting',
                    'percent': 100.0,
                    'speed': '',
                    'eta': '',
                    'title': current_title[0],
                    'message': 'Convirtiendo a MP3 e incrustando carátula...'
                })

    outtmpl_pattern = os.path.join(output_folder, "%(title)s.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'ffmpeg_location': TOOLS_DIR,
        'remote_components': ['ejs:github'],
        'js_runtimes': {'node': {}},
        'outtmpl': outtmpl_pattern,
        'writethumbnail': True,
        'windowsfilenames': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            },
            {
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False,
            }
        ],
        'progress_hooks': [ytdl_hook],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Determinar el nombre final del archivo generado
            title = info.get('title', 'cancion')
            sanitized = sanitize_filename(title)
            expected_mp3 = os.path.join(output_folder, f"{sanitized}.mp3")
            
            # Buscar el archivo generado si el sanitizado difiere levemente
            final_path = None
            if os.path.exists(expected_mp3):
                final_path = expected_mp3
            else:
                # Comprobar entre los archivos descargados o en la carpeta
                for root, _, files in os.walk(output_folder):
                    for f in files:
                        if f.endswith('.mp3'):
                            candidate = os.path.join(root, f)
                            if candidate not in downloaded_files:
                                final_path = candidate
                if not final_path and downloaded_files:
                    # Sustituir extensión a mp3
                    cand = os.path.splitext(downloaded_files[0])[0] + ".mp3"
                    if os.path.exists(cand):
                        final_path = cand

            if progress_callback:
                progress_callback({
                    'status': 'finished',
                    'percent': 100.0,
                    'speed': '',
                    'eta': '',
                    'title': title,
                    'filepath': final_path or expected_mp3
                })

            return {
                "success": True,
                "title": title,
                "uploader": info.get('uploader') or info.get('artist') or '',
                "filepath": final_path or expected_mp3,
                "error": None
            }

    except Exception as e:
        if progress_callback:
            progress_callback({
                'status': 'error',
                'percent': 0.0,
                'speed': '',
                'eta': '',
                'title': current_title[0],
                'error': str(e)
            })
        return {
            "success": False,
            "title": current_title[0],
            "filepath": None,
            "error": str(e)
        }
