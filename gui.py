import os
import sys
import json
import io
import urllib.request
import threading
import queue
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image

# Ensure the application directory is in sys.path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Import local modules
from core.downloader import get_video_info, download_audio
from core.server import state as server_state, start_server_thread

# CustomTkinter base configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = os.path.join(APP_DIR, "config.json")
DEFAULT_MUSIC_DIR = os.path.join(os.path.expanduser("~"), "Music", "YouTube MP3")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "output_folder": DEFAULT_MUSIC_DIR,
        "quality": "320"
    }

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
    except Exception:
        pass


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube to MP3 - Audio Downloader")
        self.geometry("760x780")
        self.minsize(680, 640)

        # Load configuration
        self.config_data = load_config()
        self.output_folder = self.config_data.get("output_folder", DEFAULT_MUSIC_DIR)
        self.quality = self.config_data.get("quality", "320")

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder, exist_ok=True)

        server_state.output_folder = self.output_folder

        # Task queues & state
        self.download_queue = queue.Queue()
        self.is_downloading = False
        self.current_preview_url = ""

        # Build user interface
        self.build_ui()

        # Start backend API server for the Chrome extension
        self.server_thread = None
        self.start_backend_server()

        # Download queue polling loop
        self.after(500, self.check_queue_loop)

    def build_ui(self):
        # Main scrollable container
        self.main_container = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Header
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="#18181b", corner_radius=12)
        self.header_frame.pack(fill="x", pady=(0, 15), ipady=8)

        header_content = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_content.pack(fill="x", padx=15, pady=5)

        title_box = ctk.CTkFrame(header_content, fg_color="transparent")
        title_box.pack(side="left")

        self.lbl_title = ctk.CTkLabel(
            title_box, 
            text="🎵 YouTube to MP3 Downloader", 
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#ffffff"
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_subtitle = ctk.CTkLabel(
            title_box, 
            text="Download songs in high-fidelity MP3 (up to 320 kbps) with embedded album art", 
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        )
        self.lbl_subtitle.pack(anchor="w")

        # Chrome Extension Status Badge
        self.badge_frame = ctk.CTkFrame(header_content, fg_color="#27272a", corner_radius=20)
        self.badge_frame.pack(side="right", padx=(10, 0), pady=5)

        self.lbl_badge = ctk.CTkLabel(
            self.badge_frame,
            text="🟢 Chrome Extension: Ready",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#4ade80",
            padx=12,
            pady=4
        )
        self.lbl_badge.pack()

        # 2. URL Input Card
        self.input_card = ctk.CTkFrame(self.main_container, fg_color="#202023", corner_radius=12)
        self.input_card.pack(fill="x", pady=(0, 15), padx=2, ipady=5)

        lbl_input = ctk.CTkLabel(
            self.input_card, 
            text="🔗 YouTube Video or Song URL:", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#f4f4f5"
        )
        lbl_input.pack(anchor="w", padx=15, pady=(10, 5))

        entry_box = ctk.CTkFrame(self.input_card, fg_color="transparent")
        entry_box.pack(fill="x", padx=15, pady=(0, 10))

        self.entry_url = ctk.CTkEntry(
            entry_box, 
            placeholder_text="https://www.youtube.com/watch?v=...", 
            height=40,
            font=ctk.CTkFont(size=13),
            corner_radius=8
        )
        self.entry_url.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_url.bind("<Return>", lambda e: self.on_url_submitted())

        self.btn_paste = ctk.CTkButton(
            entry_box, 
            text="📋 Paste", 
            width=80, 
            height=40,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.paste_from_clipboard
        )
        self.btn_paste.pack(side="left", padx=(0, 6))

        self.btn_clear = ctk.CTkButton(
            entry_box, 
            text="✖", 
            width=40, 
            height=40,
            fg_color="#3f3f46",
            hover_color="#52525b",
            font=ctk.CTkFont(size=13),
            command=self.clear_input
        )
        self.btn_clear.pack(side="left")

        # 3. Preview Card (Thumbnail + Metadata)
        self.preview_card = ctk.CTkFrame(self.main_container, fg_color="#18181b", corner_radius=12)
        self.preview_card.pack(fill="x", pady=(0, 15), padx=2)

        self.preview_content = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        self.preview_content.pack(fill="x", padx=12, pady=12)

        # Thumbnail Image
        self.lbl_thumb = ctk.CTkLabel(
            self.preview_content, 
            text="🎵\nNo video selected", 
            width=140, 
            height=90, 
            fg_color="#27272a", 
            corner_radius=8,
            font=ctk.CTkFont(size=12)
        )
        self.lbl_thumb.pack(side="left", padx=(0, 12))

        # Metadata Box
        self.info_box = ctk.CTkFrame(self.preview_content, fg_color="transparent")
        self.info_box.pack(side="left", fill="both", expand=True)

        self.lbl_preview_title = ctk.CTkLabel(
            self.info_box, 
            text="Paste a link to view song details", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#f4f4f5",
            anchor="w",
            wraplength=450,
            justify="left"
        )
        self.lbl_preview_title.pack(fill="x", anchor="w")

        self.lbl_preview_channel = ctk.CTkLabel(
            self.info_box, 
            text="Channel / Artist: --", 
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa",
            anchor="w"
        )
        self.lbl_preview_channel.pack(fill="x", anchor="w", pady=(2, 0))

        self.lbl_preview_duration = ctk.CTkLabel(
            self.info_box, 
            text="Duration: --:--", 
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa",
            anchor="w"
        )
        self.lbl_preview_duration.pack(fill="x", anchor="w", pady=(2, 0))

        # 4. Settings Card (Quality + Output Folder)
        self.settings_card = ctk.CTkFrame(self.main_container, fg_color="#202023", corner_radius=12)
        self.settings_card.pack(fill="x", pady=(0, 15), padx=2, ipady=5)

        settings_grid = ctk.CTkFrame(self.settings_card, fg_color="transparent")
        settings_grid.pack(fill="x", padx=15, pady=10)

        # Quality
        lbl_quality = ctk.CTkLabel(
            settings_grid, 
            text="MP3 Quality:", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        lbl_quality.grid(row=0, column=0, sticky="w", pady=(0, 8), padx=(0, 10))

        self.quality_var = ctk.StringVar(value=f"{self.quality} kbps")
        self.combo_quality = ctk.CTkOptionMenu(
            settings_grid,
            values=["320 kbps (Maximum Quality)", "256 kbps (High Quality)", "192 kbps (Standard)", "128 kbps (Lightweight)"],
            command=self.on_quality_changed,
            width=230,
            height=32,
            corner_radius=8
        )
        for opt in ["320 kbps (Maximum Quality)", "256 kbps (High Quality)", "192 kbps (Standard)", "128 kbps (Lightweight)"]:
            if opt.startswith(self.quality):
                self.combo_quality.set(opt)
                break
        self.combo_quality.grid(row=0, column=1, sticky="w", pady=(0, 8))

        # Folder
        lbl_folder = ctk.CTkLabel(
            settings_grid, 
            text="Save to:", 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        lbl_folder.grid(row=1, column=0, sticky="w", padx=(0, 10))

        folder_actions = ctk.CTkFrame(settings_grid, fg_color="transparent")
        folder_actions.grid(row=1, column=1, sticky="w", columnspan=2)

        self.lbl_folder_path = ctk.CTkLabel(
            folder_actions, 
            text=self.shorten_path(self.output_folder, 36), 
            font=ctk.CTkFont(size=12),
            text_color="#93c5fd"
        )
        self.lbl_folder_path.pack(side="left", padx=(0, 10))

        self.btn_browse = ctk.CTkButton(
            folder_actions, 
            text="📁 Browse", 
            width=80, 
            height=30,
            fg_color="#374151",
            hover_color="#4b5563",
            font=ctk.CTkFont(size=12),
            command=self.choose_folder
        )
        self.btn_browse.pack(side="left", padx=(0, 6))

        self.btn_open_folder = ctk.CTkButton(
            folder_actions, 
            text="📂 Open Folder", 
            width=95, 
            height=30,
            fg_color="#059669",
            hover_color="#047857",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.open_output_folder
        )
        self.btn_open_folder.pack(side="left")

        # 5. Main Action Button & Progress
        self.action_card = ctk.CTkFrame(self.main_container, fg_color="#18181b", corner_radius=12)
        self.action_card.pack(fill="x", pady=(0, 15), padx=2, ipady=8)

        self.btn_download = ctk.CTkButton(
            self.action_card,
            text="⬇️ DOWNLOAD SONG AS MP3",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            corner_radius=10,
            command=self.start_download_from_gui
        )
        self.btn_download.pack(fill="x", padx=15, pady=(12, 10))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.action_card, height=12, corner_radius=6)
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 6))

        self.lbl_status = ctk.CTkLabel(
            self.action_card,
            text="Ready to download any song.",
            font=ctk.CTkFont(size=13),
            text_color="#d4d4d8"
        )
        self.lbl_status.pack(pady=(0, 10))

        # 6. Download History
        self.history_card = ctk.CTkFrame(self.main_container, fg_color="#202023", corner_radius=12)
        self.history_card.pack(fill="both", expand=True, padx=2, pady=(0, 10))

        lbl_hist = ctk.CTkLabel(
            self.history_card, 
            text="🎵 Recently Downloaded Songs:", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#f4f4f5"
        )
        lbl_hist.pack(anchor="w", padx=15, pady=(10, 6))

        self.history_list = ctk.CTkFrame(self.history_card, fg_color="transparent")
        self.history_list.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self.history_empty_lbl = ctk.CTkLabel(
            self.history_list, 
            text="No songs downloaded in this session yet.", 
            text_color="#71717a",
            font=ctk.CTkFont(size=12, slant="italic")
        )
        self.history_empty_lbl.pack(pady=15)

    def shorten_path(self, path: str, max_chars: int = 40) -> str:
        if len(path) <= max_chars:
            return path
        return path[:15] + "..." + path[-(max_chars - 18):]

    def paste_from_clipboard(self):
        try:
            clipboard_text = self.clipboard_get().strip()
            if clipboard_text:
                self.entry_url.delete(0, tk.END)
                self.entry_url.insert(0, clipboard_text)
                self.on_url_submitted()
        except Exception:
            pass

    def clear_input(self):
        self.entry_url.delete(0, tk.END)
        self.current_preview_url = ""
        self.lbl_preview_title.configure(text="Paste a link to view song details")
        self.lbl_preview_channel.configure(text="Channel / Artist: --")
        self.lbl_preview_duration.configure(text="Duration: --:--")
        self.lbl_thumb.configure(image=None, text="🎵\nNo video selected")

    def on_url_submitted(self):
        url = self.entry_url.get().strip()
        if not url or ("youtube.com" not in url and "youtu.be" not in url):
            return
        if url == self.current_preview_url:
            return

        self.current_preview_url = url
        self.lbl_preview_title.configure(text="🔍 Fetching video details...")
        threading.Thread(target=self._fetch_preview_thread, args=(url,), daemon=True).start()

    def _fetch_preview_thread(self, url):
        info = get_video_info(url)
        self.after(0, self._update_preview_ui, info)

    def _update_preview_ui(self, info):
        if not info.get("success"):
            self.lbl_preview_title.configure(text="⚠️ Could not fetch preview details (will still attempt download)")
            return

        title = info.get("title", "Song")
        if info.get("is_playlist"):
            title = f"📂 [Playlist: {info.get('item_count')} tracks] {title}"

        self.lbl_preview_title.configure(text=title)
        self.lbl_preview_channel.configure(text=f"Channel / Artist: {info.get('uploader', 'Unknown')}")
        self.lbl_preview_duration.configure(text=f"Duration: {info.get('duration_str', '--:--')}")

        thumb_url = info.get("thumbnail")
        if thumb_url:
            threading.Thread(target=self._load_thumb_image, args=(thumb_url,), daemon=True).start()

    def _load_thumb_image(self, thumb_url):
        try:
            req = urllib.request.Request(thumb_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                img_data = response.read()
            pil_img = Image.open(io.BytesIO(img_data))
            pil_img = pil_img.resize((150, 85), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(150, 85))
            self.after(0, lambda: self.lbl_thumb.configure(image=ctk_img, text=""))
        except Exception:
            pass

    def on_quality_changed(self, choice):
        q = choice.split()[0]
        self.quality = q
        self.config_data["quality"] = q
        save_config(self.config_data)

    def choose_folder(self):
        new_dir = filedialog.askdirectory(initialdir=self.output_folder, title="Select folder to save MP3 files")
        if new_dir:
            self.output_folder = new_dir
            self.config_data["output_folder"] = new_dir
            save_config(self.config_data)
            server_state.output_folder = new_dir
            self.lbl_folder_path.configure(text=self.shorten_path(new_dir, 36))

    def open_output_folder(self):
        if os.path.exists(self.output_folder):
            subprocess.Popen(f'explorer "{os.path.abspath(self.output_folder)}"')

    def queue_download(self, url: str, quality: str = "320"):
        self.download_queue.put((url, quality))

    def start_download_from_gui(self):
        url = self.entry_url.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Please enter a YouTube link before downloading.")
            return
        self.btn_download.configure(state="disabled", text="⏳ Adding to queue...")
        self.queue_download(url, self.quality)

    def check_queue_loop(self):
        if not self.is_downloading and not self.download_queue.empty():
            url, quality = self.download_queue.get()
            self.is_downloading = True
            self.btn_download.configure(state="disabled", text="⏳ Downloading...")
            self.progress_bar.set(0.0)
            self.lbl_status.configure(text="Connecting to YouTube...", text_color="#38bdf8")
            threading.Thread(target=self._run_download_worker, args=(url, quality), daemon=True).start()

        self.after(500, self.check_queue_loop)

    def _run_download_worker(self, url, quality):
        def on_progress(pdata):
            self.after(0, self._update_progress_ui, pdata)
            server_state.update_progress(pdata)

        res = download_audio(url, self.output_folder, quality=quality, progress_callback=on_progress)
        self.after(0, self._on_download_complete, res)

    def _update_progress_ui(self, pdata):
        status = pdata.get('status')
        if status == 'downloading':
            pct = pdata.get('percent', 0.0)
            self.progress_bar.set(pct / 100.0)
            speed = pdata.get('speed', '')
            eta = pdata.get('eta', '')
            self.lbl_status.configure(
                text=f"Downloading: {pct:.1f}% | Speed: {speed} | Remaining: {eta}",
                text_color="#38bdf8"
            )
        elif status == 'converting':
            self.progress_bar.set(1.0)
            self.lbl_status.configure(
                text="🎵 Converting to MP3 & embedding album art and metadata...",
                text_color="#fbbf24"
            )
        elif status == 'error':
            self.progress_bar.set(0.0)
            err = pdata.get('error', 'Unknown error')
            self.lbl_status.configure(text=f"❌ Error: {err[:80]}", text_color="#ef4444")

    def _on_download_complete(self, res):
        self.is_downloading = False
        self.btn_download.configure(state="normal", text="⬇️ DOWNLOAD SONG AS MP3")

        if res.get("success"):
            self.progress_bar.set(1.0)
            title = res.get("title", "Song")
            filepath = res.get("filepath")
            self.lbl_status.configure(
                text=f"✅ Download complete! Saved as MP3.",
                text_color="#4ade80"
            )
            self.add_to_history(title, filepath)
        else:
            err = res.get("error", "Unknown error")
            self.lbl_status.configure(
                text=f"❌ Download failed: {err[:90]}",
                text_color="#ef4444"
            )

    def add_to_history(self, title: str, filepath: str):
        if self.history_empty_lbl.winfo_exists():
            self.history_empty_lbl.pack_forget()

        item_row = ctk.CTkFrame(self.history_list, fg_color="#18181b", corner_radius=8)
        item_row.pack(fill="x", pady=4, ipady=4)

        lbl_song = ctk.CTkLabel(
            item_row,
            text=f"🎶 {title}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f4f4f5",
            anchor="w"
        )
        lbl_song.pack(side="left", padx=10, fill="x", expand=True)

        if filepath and os.path.exists(filepath):
            btn_play = ctk.CTkButton(
                item_row,
                text="▶️ Play",
                width=85,
                height=28,
                fg_color="#2563eb",
                hover_color="#1d4ed8",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda p=filepath: os.startfile(p)
            )
            btn_play.pack(side="right", padx=(4, 8))

            btn_open = ctk.CTkButton(
                item_row,
                text="📁 Show File",
                width=85,
                height=28,
                fg_color="#3f3f46",
                hover_color="#52525b",
                font=ctk.CTkFont(size=11),
                command=lambda p=filepath: subprocess.Popen(f'explorer /select,"{os.path.abspath(p)}"')
            )
            btn_open.pack(side="right", padx=4)

    def start_backend_server(self):
        """Starts the local backend server for the Chrome Extension."""
        try:
            start_server_thread(
                download_callback=lambda url, q: self.after(0, self.on_external_download_request, url, q),
                output_folder=self.output_folder
            )
            self.lbl_badge.configure(text="🟢 Chrome Extension: Ready", text_color="#4ade80")
        except Exception:
            self.lbl_badge.configure(text="🟡 Server Offline", text_color="#facc15")

    def on_external_download_request(self, url: str, quality: str):
        """Triggered when the Chrome extension sends a download request."""
        self.entry_url.delete(0, tk.END)
        self.entry_url.insert(0, url)
        self.on_url_submitted()
        self.queue_download(url, quality or self.quality)
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)


def run_app():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    run_app()
