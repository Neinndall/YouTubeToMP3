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
        showToast("<b>¡Descarga iniciada!</b> La app de escritorio está descargando la canción en MP3 (320 kbps) con carátula.", "success");
      } else {
        const err = await response.json();
        showToast(`Error al iniciar la descarga: ${err.error || "Desconocido"}`, "error");
      }
    } catch (e) {
      showToast(
        "<b>La app de escritorio no está abierta.</b><br>Abre <i>YouTubeToMP3</i> en tu PC para descargar con 1 clic.",
        "error",
        6000
      );
    }
  }

  function injectButton() {
    if (!window.location.pathname.startsWith("/watch")) return;
    if (document.getElementById(BUTTON_ID)) return;

    // Buscar la barra de acciones de YouTube
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
    btn.title = "Descargar audio en MP3 (320 kbps con carátula)";
    btn.innerHTML = `
      <svg viewBox="0 0 24 24" width="18" height="18">
        <path d="M12 3v11.17l4.59-4.59L18 11l-6 6-6-6 1.41-1.41L11 14.17V3h1zm-7 16h14v2H5v-2z"/>
      </svg>
      <span>Descargar MP3</span>
    `;

    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      triggerDownload(window.location.href);
    });

    container.appendChild(btn);
  }

  // Eventos de navegación SPA de YouTube
  window.addEventListener("yt-navigate-finish", () => {
    setTimeout(injectButton, 600);
    setTimeout(injectButton, 1500);
  });

  // Observador de cambios en el DOM
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

  // Intento inicial
  setTimeout(injectButton, 800);
})();
