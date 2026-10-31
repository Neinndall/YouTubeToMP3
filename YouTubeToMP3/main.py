import os
import sys
import time
import queue
import threading

# Prevent any child process (FFmpeg, Node.js, etc.) from flashing a black CMD console
if sys.platform == 'win32':
    import subprocess
    _orig_popen = subprocess.Popen
    def _silent_popen(*args, **kwargs):
        kwargs['creationflags'] = kwargs.get('creationflags', 0) | subprocess.CREATE_NO_WINDOW
        return _orig_popen(*args, **kwargs)
    subprocess.Popen = _silent_popen

# Ensure the root application directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Add tools directory to PATH
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
if os.path.exists(TOOLS_DIR) and TOOLS_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] = TOOLS_DIR + os.pathsep + os.environ.get("PATH", "")

from core.downloader import download_audio
from core.server import state as server_state, start_server_thread
from gui import load_config, DEFAULT_MUSIC_DIR

def run_headless_service():
    """Runs a silent background daemon for managing downloads via Chrome Extension only."""
    cfg = load_config()
    output_folder = cfg.get("output_folder", DEFAULT_MUSIC_DIR)
    default_quality = cfg.get("quality", "320")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)

    server_state.output_folder = output_folder
    task_queue = queue.Queue()

    def enqueue_download(url, quality):
        task_queue.put((url, quality or default_quality))

    start_server_thread(download_callback=enqueue_download, output_folder=output_folder)
    print(f"[YouTubeToMP3] Headless background service started on port 48123.")
    print(f"[YouTubeToMP3] Saving downloads to: {output_folder}")

    try:
        while True:
            url, quality = task_queue.get()
            print(f"[YouTubeToMP3] Processing download: {url} ({quality} kbps)")

            def on_progress(pdata):
                server_state.update_progress(pdata)

            res = download_audio(url, output_folder, quality=quality, progress_callback=on_progress)
            if res.get("success"):
                print(f"[YouTubeToMP3] Successfully downloaded: {res.get('title')}")
            else:
                print(f"[YouTubeToMP3] Error: {res.get('error')}")

            task_queue.task_done()
    except (KeyboardInterrupt, SystemExit):
        print("[YouTubeToMP3] Service stopping...")


if __name__ == "__main__":
    if "--headless" in sys.argv or "--service" in sys.argv or "-b" in sys.argv:
        run_headless_service()
    else:
        from gui import run_app
        run_app()
