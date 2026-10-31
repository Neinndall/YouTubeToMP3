// YouTube to MP3 - Content Script
(function () {
  const SERVER_URL = "http://127.0.0.1:48123";
  const BUTTON_ID = "yt-mp3-quick-download-btn";

  function showToast(message, type = "success", duration = 4500) {
    const existing = document.querySelector(".yt-mp3-toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.className = `yt-mp3-toast ${type}`;
    toast.innerHTML = `
      <div style="font-size: 18px;">${type === "success" ? "🎵" : "⚠️"}</div>
      <div style="line-height: 1.4;">${message}</div>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      toast.style.opacity = "0";
      toast.style.transform = "translateY(15px)";
      setTimeout(() => toast.remove(), 400);
    }, duration);
  }

  async function triggerDownload(url) {
    try {
      const response = await fetch(`${SERVER_URL}/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url, quality: "320" }),
      });

      if (response.ok) {
        showToast("<b>Download started!</b> The desktop helper is converting the audio to MP3 (320 kbps) with album art.", "success");
      } else {
        const err = await response.json();
        showToast(`Download error: ${err.error || "Unknown"}`, "error");
      }
    } catch (e) {
      showToast(
        "<b>YouTubeToMP3 helper is not running.</b><br>Please start <i>YouTubeToMP3</i> on your PC to download with 1 click.",
        "error",
        6000
      );
    }
  }

  function injectButton() {
    if (!window.location.pathname.startsWith("/watch")) return;
    if (document.getElementById(BUTTON_ID)) return;

    // Search for YouTube action buttons container
    const targetContainers = [
      "#actions #top-level-buttons-computed",
      "#top-level-buttons-computed",
      "ytd-watch-metadata #actions ytd-menu-renderer",
      "#actions-inner #top-level-buttons-computed",
      "#menu #top-level-buttons-computed"
    ];

    let container = null;
    for (const selector of targetContainers) {
      const el = document.querySelector(selector);
      if (el) {
        container = el;
        break;
      }
    }

    if (!container) return;

    const btn = document.createElement("button");
    btn.id = BUTTON_ID;
    btn.className = "yt-mp3-download-btn";
    btn.title = "Download audio as MP3 (320 kbps with album art)";
    btn.innerHTML = `
      <svg viewBox="0 0 24 24" width="18" height="18">
        <path d="M12 3v11.17l4.59-4.59L18 11l-6 6-6-6 1.41-1.41L11 14.17V3h1zm-7 16h14v2H5v-2z"/>
      </svg>
      <span>Download MP3</span>
    `;

    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      triggerDownload(window.location.href);
    });

    container.appendChild(btn);
  }

  // Handle YouTube SPA dynamic navigation events
  window.addEventListener("yt-navigate-finish", () => {
    setTimeout(injectButton, 600);
    setTimeout(injectButton, 1500);
  });

  // DOM mutation observer for dynamic rendering
  let debounceTimer = null;
  const observer = new MutationObserver(() => {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      if (window.location.pathname.startsWith("/watch") && !document.getElementById(BUTTON_ID)) {
        injectButton();
      }
    }, 400);
  });

  observer.observe(document.body, { childList: true, subtree: true });

  // Initial attempt
  setTimeout(injectButton, 800);
})();
