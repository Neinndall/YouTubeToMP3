# 🎵 YouTube to MP3 Downloader Pro

A fast, lightweight, and modern **YouTube to MP3 audio downloader** featuring a native Windows **Desktop App (`YouTubeToMP3.exe`)** and a companion **Google Chrome Extension (Manifest V3)** for 1-click downloads with up to **320 kbps** audio quality, embedded high-resolution album art, and full ID3 metadata.

---

## 🚀 Key Features

- **Highest Audio Quality**: Converts audio to true high-bitrate MP3 (320 kbps, 256 kbps, 192 kbps, or 128 kbps) using embedded FFmpeg.
- **Embedded HD Album Art & ID3 Tags**: Automatically fetches original high-res thumbnails and tags (Title, Artist, Channel, Year) and embeds them directly into the `.mp3` file. Compatible with Windows Media Player, Groove, VLC, Spotify local files, and mobile/car audio players.
- **Chrome Extension (1-Click Download)**: Injects a native-looking `[ 🎵 Download MP3 ]` button right into YouTube's action bar under any video, plus an intuitive popup menu.
- **Zero-Console Clean Launch**: Opens directly without any command prompt (`cmd.exe`) or black window flashing.
- **Headless Background Service**: Want to manage everything directly from Google Chrome without any desktop window open? Run the silent background service and control all downloads 100% inside your browser!
- **Modern Desktop GUI**: Sleek dark-mode interface built with CustomTkinter, clipboard auto-paste, live download progress (speed, percentage, ETA), and built-in music player launcher.
- **Privacy & Ad-Free**: Runs 100% locally on your machine. No suspicious web converters, no popups, no tracking.

---

## ❓ Can it be managed entirely from the Chrome Extension?

**Yes!** 

### Why can't a browser extension download YouTube audio on its own?
Browser extensions are strictly sandboxed by Chrome:
1. **YouTube Dynamic Cipher Protection**: YouTube regularly scrambles audio streaming URLs (`n-sig` and JS challenge tokens). Without an automated solver like `yt-dlp`, browser requests fail with 403 Forbidden or heavy throttling.
2. **Audio Conversion & Tagging**: YouTube provides audio in Opus (WebM) or AAC (M4A). Producing authentic MP3 files with high-res embedded ID3 cover art requires FFmpeg. Running FFmpeg in WebAssembly inside Chrome's memory is slow, consumes gigabytes of RAM, and cannot write to custom local music folders.
3. **Chrome Web Store Policy**: Google strictly forbids extensions that download YouTube videos from the Chrome Web Store.

### The Solution: Silent Background Mode
With our hybrid architecture, you **never** need to look at or interact with the desktop window if you prefer not to:
1. Run `start_background_service.vbs` inside `YouTubeToMP3/`. The helper runs completely invisibly in the background.
2. Open YouTube in Google Chrome.
3. Click the **"Download MP3"** button under any video, or use the Extension Popup.
4. The file is downloaded in maximum 320 kbps quality and saved straight to your Music folder!

---

## 📦 Getting Started

### 1. Prerequisites
- **Windows 10 / 11**
- **Python 3.10+**
- **Node.js** (for YouTube JS challenge resolution)

Install required Python libraries:
```bash
cd YouTubeToMP3
pip install -r requirements.txt
```

*(Note: FFmpeg and FFprobe binaries are already bundled inside the `tools/` folder).*

---

### 2. Launch Options

Inside the `YouTubeToMP3/` folder:

| File | Description |
| :--- | :--- |
| **`YouTubeToMP3.exe`** | **Native Windows App**: Double-click to launch the GUI directly with **zero CMD / terminal windows**. |
| **`launch_gui_silent.vbs`** | Launches the Desktop GUI silently via VBScript without a terminal window. |
| **`launch_gui.bat`** | Launches the Desktop GUI with console output (ideal for debugging). |
| **`start_background_service.vbs`** | Launches the **silent background daemon** so you can manage downloads exclusively via Chrome. |
| **`stop_background_service.bat`** | Stops the background service at any time. |

---

## 🧩 Installing the Chrome Extension (3 Steps)

1. Open **Google Chrome** and navigate to:
   ```text
   chrome://extensions/
   ```
2. Enable **Developer mode** in the top-right corner.
3. Click **Load unpacked** (Cargar descomprimida) and select the `extension` folder inside `YouTubeToMP3`:
   ```text
   ...\YouTubeToMP3\YouTubeToMP3\extension
   ```

Now, whenever you browse any YouTube video, a red **`Download MP3`** button will appear right next to the "Like" and "Share" buttons!

---

## 📁 Default Output Directory

By default, downloaded MP3s are saved in:
```text
C:\Users\<Your-Username>\Music\YouTube MP3
```
*You can customize the destination folder at any time directly in the Desktop GUI or configuration.*

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
