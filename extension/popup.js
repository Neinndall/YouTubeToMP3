const SERVER_URL = "http://127.0.0.1:48123";

let currentVideoUrl = "";
let isServerOnline = false;
let pollingInterval = null;

const statusBadge = document.getElementById("statusBadge");
const statusText = document.getElementById("statusText");
const videoCard = document.getElementById("videoCard");
const manualCard = document.getElementById("manualCard");
const videoThumb = document.getElementById("videoThumb");
const videoTitle = document.getElementById("videoTitle");
const videoDuration = document.getElementById("videoDuration");
const inputUrl = document.getElementById("inputUrl");
const selectQuality = document.getElementById("selectQuality");
const btnDownload = document.getElementById("btnDownload");
const progressBox = document.getElementById("progressBox");
const progressBar = document.getElementById("progressBar");
const lblProgress = document.getElementById("lblProgress");
const btnOpenFolder = document.getElementById("btnOpenFolder");
const offlineNotice = document.getElementById("appOfflineNotice");

async function checkServerStatus() {
  try {
    const res = await fetch(`${SERVER_URL}/ping`, { method: "GET" });
    if (res.ok) {
      setServerState(true);
      return true;
    }
  } catch (e) {
    setServerState(false);
  }
  return false;
}

function setServerState(online) {
  isServerOnline = online;
  if (online) {
    statusBadge.className = "status-badge online";
    statusText.textContent = "App Conectada";
    offlineNotice.classList.add("hidden");
    btnDownload.disabled = false;
  } else {
    statusBadge.className = "status-badge offline";
    statusText.textContent = "Desconectado";
    offlineNotice.classList.remove("hidden");
  }
}

async function detectCurrentTab() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url && (tab.url.includes("youtube.com/watch") || tab.url.includes("youtu.be/"))) {
      currentVideoUrl = tab.url;
      videoCard.classList.remove("hidden");
      manualCard.classList.add("hidden");

      videoTitle.textContent = tab.title ? tab.title.replace(" - YouTube", "") : "Vídeo de YouTube";

      // Extraer video ID para miniatura
      const match = tab.url.match(/(?:v=|\/)([a-zA-Z0-9_-]{11})/);
      if (match && match[1]) {
        const vidId = match[1];
        videoThumb.src = `https://img.youtube.com/vi/${vidId}/mqdefault.jpg`;
      }
    } else {
      videoCard.classList.add("hidden");
      manualCard.classList.remove("hidden");
    }
  } catch (e) {
    videoCard.classList.add("hidden");
    manualCard.classList.remove("hidden");
  }
}

async function startDownload() {
  const url = currentVideoUrl || inputUrl.value.trim();
  if (!url) {
    alert("Por favor ingresa o abre un enlace de YouTube.");
    return;
  }

  const quality = selectQuality.value;

  btnDownload.disabled = true;
  btnDownload.innerHTML = "<span>⏳</span> Enviando descarga...";

  try {
    const res = await fetch(`${SERVER_URL}/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url, quality: quality }),
    });

    if (res.ok) {
      progressBox.classList.remove("hidden");
      lblProgress.textContent = "Iniciando descarga...";
      progressBar.style.width = "10%";
      startStatusPolling();
    } else {
      const err = await res.json();
      alert("Error: " + (err.error || "No se pudo iniciar la descarga"));
      btnDownload.disabled = false;
      btnDownload.innerHTML = "<span>⬇️</span> Descargar en MP3";
    }
  } catch (e) {
    alert("No se pudo conectar con la aplicación de escritorio. Asegúrate de tenerla abierta.");
    btnDownload.disabled = false;
    btnDownload.innerHTML = "<span>⬇️</span> Descargar en MP3";
  }
}

function startStatusPolling() {
  if (pollingInterval) clearInterval(pollingInterval);

  pollingInterval = setInterval(async () => {
    try {
      const res = await fetch(`${SERVER_URL}/status`);
      if (res.ok) {
        const data = await res.json();
        if (data.is_downloading) {
          const pct = Math.max(5, Math.min(100, data.progress));
          progressBar.style.width = `${pct}%`;
          lblProgress.textContent = `${data.status_message} (${pct.toFixed(0)}%)`;
        } else if (data.status_message === "¡Descarga completada!") {
          progressBar.style.width = "100%";
          lblProgress.textContent = "✅ ¡Descarga completada con éxito!";
          btnDownload.disabled = false;
          btnDownload.innerHTML = "<span>⬇️</span> Descargar en MP3";
          clearInterval(pollingInterval);
        }
      }
    } catch (e) {
      clearInterval(pollingInterval);
    }
  }, 800);
}

btnDownload.addEventListener("click", startDownload);

btnOpenFolder.addEventListener("click", async () => {
  try {
    await fetch(`${SERVER_URL}/open_folder`, { method: "POST" });
  } catch (e) {
    alert("Abre la app de escritorio para acceder directamente a la carpeta.");
  }
});

// Inicialización
detectCurrentTab();
checkServerStatus();
setInterval(checkServerStatus, 3000);
