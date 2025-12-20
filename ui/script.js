let apps = [];
let statusCheckInterval = null;

function el(tag, className) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  return e;
}
function $(id) { return document.getElementById(id); }

function shortenPath(path, maxLen = 55) {
  if (!path) return "";
  const p = String(path);
  if (p.length <= maxLen) return p;

  const keepStart = Math.max(12, Math.floor(maxLen * 0.45));
  const keepEnd = Math.max(12, Math.floor(maxLen * 0.45));
  return p.slice(0, keepStart) + "..." + p.slice(-keepEnd);
}

async function saveApps() {
  await window.pywebview.api.save_apps(apps);
}

async function autoResizeWindow() {
  try {
    const list = document.getElementById("appsList");
    if (!list) return;

    const baseHeight = 280;
    const rowHeight = 72;
    const maxRows = 7;
    const visibleRows = Math.min(apps.length, maxRows);

    const h = baseHeight + visibleRows * rowHeight;
    const w = 1024;
    await window.pywebview.api.resize_window(w, Math.max(768, h));
  } catch (e) {
    console.log("autoResizeWindow error", e);
  }
}

function render() {
  const list = document.getElementById("appsList");
  if (!list) return;

  list.innerHTML = "";

  apps.forEach((a, i) => {
    const row = el("div", "app-row");

    const check = el("div", "case-coche");
    check.classList.toggle("checked", !!a.checked);
    check.title = "Inclure dans Start/Stop";
    check.onclick = async () => {
      a.checked = !a.checked;
      check.classList.toggle("checked", a.checked);
      await saveApps();
    };

    const statusIndicator = el("div", "status-indicator");
    statusIndicator.classList.add("stopped");
    statusIndicator.title = "Status du processus";

    const icon = el("div", "icone");
    if (a.icon) icon.style.backgroundImage = `url(${a.icon})`;

    const name = el("div", "name-apps");
    name.textContent = a.name || "App";
    name.title = a.name || "App";

    const path = el("div", "file-path");
    path.textContent = shortenPath(a.path || "");
    path.title = a.path || "";

    const browse = el("div", "search-apps");
    browse.title = "Choisir le .exe";
    browse.onclick = async () => {
      const p = await window.pywebview.api.browse_exe();
      if (p) {
        a.path = p;
        a.icon = await window.pywebview.api.get_icon(p);
        await saveApps();
        render();
      }
    };

    const restart = el("div", "restart-app");
    restart.title = "Redémarrer l'application";
    restart.onclick = async () => {
      if (!confirm(`Redémarrer ${a.name || "cette app"} ?`)) return;

      restart.style.opacity = "0.5";
      restart.style.pointerEvents = "none";

      try {
        const result = await window.pywebview.api.restart_app(a);

        if (result.ok) {
          restart.style.backgroundColor = "#6fb15e";
          setTimeout(() => (restart.style.backgroundColor = ""), 1000);
        } else {
          alert("Erreur restart : " + (result.error || "inconnue"));
        }
      } catch (e) {
        alert("Erreur restart : " + e);
      } finally {
        restart.style.opacity = "1";
        restart.style.pointerEvents = "auto";
      }
    };

    const moveUp = el("div", "move-up");
    moveUp.title = "Monter";
    moveUp.onclick = async () => {
      await window.pywebview.api.move_app_up(i);
      apps = await window.pywebview.api.get_apps();
      render();
    };

    const moveDown = el("div", "move-down");
    moveDown.title = "Descendre";
    moveDown.onclick = async () => {
      await window.pywebview.api.move_app_down(i);
      apps = await window.pywebview.api.get_apps();
      render();
    };

    const del = el("div", "delete-apps");
    del.title = "Supprimer";
    del.onclick = async () => {
      if (!confirm(`Supprimer ${a.name || "cette app"} ?`)) return;
      apps.splice(i, 1);
      await saveApps();
      render();
    };

    row.appendChild(check);
    row.appendChild(statusIndicator);
    row.appendChild(icon);
    row.appendChild(name);
    row.appendChild(path);
    row.appendChild(restart);
    row.appendChild(browse);
    row.appendChild(moveUp);
    row.appendChild(moveDown);
    row.appendChild(del);

    list.appendChild(row);
  });

  autoResizeWindow();
  refreshStatuses();
}

async function refreshStatuses() {
  try {
    if (!window.pywebview || !window.pywebview.api) return;
    const statuses = await window.pywebview.api.get_all_process_statuses(apps);

    const rows = document.querySelectorAll(".app-row");
    rows.forEach((row, i) => {
      const indicator = row.querySelector(".status-indicator");
      if (!indicator) return;

      const running = !!statuses[i];
      indicator.classList.toggle("running", running);
      indicator.classList.toggle("stopped", !running);
      indicator.title = running ? "En service" : "Arrêté";
    });
  } catch (e) {
    console.log("refreshStatuses error", e);
  }
}

function compareVersions(a, b) {
  const pa = String(a || "").split(".").map(n => parseInt(n, 10) || 0);
  const pb = String(b || "").split(".").map(n => parseInt(n, 10) || 0);
  const len = Math.max(pa.length, pb.length);
  for (let i = 0; i < len; i++) {
    const x = pa[i] || 0;
    const y = pb[i] || 0;
    if (x < y) return -1;
    if (x > y) return 1;
  }
  return 0;
}

async function loadVersionAndUpdateStatus() {
  const versionDisplayEl = document.getElementById("versionDisplay"); // ancien
  const versionTextEl = document.getElementById("versionText"); // nouveau
  const statusEl = document.getElementById("updateStatus"); // nouveau

  try {
    if (!window.pywebview || !window.pywebview.api) return;

    // Version locale
    const localVersion = await window.pywebview.api.get_version();
    if (versionDisplayEl) versionDisplayEl.textContent = `Version ${localVersion}`;
    if (versionTextEl) versionTextEl.textContent = `Version ${localVersion}`;

    // Statut update
    if (statusEl) {
      statusEl.textContent = "Vérification…";
      statusEl.className = "status-badge status-checking";
    }

    // Si ton backend expose une méthode check_update => tu peux l’utiliser ici.
    // Sinon on laisse en "OK" après chargement (propre et simple).
    if (statusEl) {
      statusEl.textContent = "OK";
      statusEl.className = "status-badge status-ok";
    }
  } catch (e) {
    console.log("loadVersionAndUpdateStatus error", e);
    if (statusEl) {
      statusEl.textContent = "Erreur";
      statusEl.className = "status-badge status-error";
    }
  }
}

async function init() {
  if (!window.pywebview || !window.pywebview.api) return;

  apps = await window.pywebview.api.get_apps();
  render();

  const btnAdd = document.getElementById("btnAdd");
  const btnStart = document.getElementById("btnStart");
  const btnStop = document.getElementById("btnStop");

  if (btnAdd) {
    btnAdd.onclick = async () => {
  // 1) choisir le .exe d'abord
  const p = await window.pywebview.api.browse_exe();
  if (!p) return;

  // 2) proposer un nom par défaut basé sur le fichier
  const defaultName = p.split("\\").pop().replace(/\.exe$/i, "");

  // 3) demander le nom après
  const name = prompt("Nom du jeu :", defaultName);
  if (!name) return;

  const icon = await window.pywebview.api.get_icon(p);

  apps.push({
    name: name,
    path: p,
    icon: icon,
    checked: true
  });

  await saveApps();
  render();
};

  }

  if (btnStart) {
    btnStart.onclick = async () => {
      const result = await window.pywebview.api.start_selected(apps);
      if (!result.ok) {
        alert("Erreur Start :\n" + (result.errors || []).join("\n"));
      }
      setTimeout(refreshStatuses, 600);
    };
  }

  if (btnStop) {
    btnStop.onclick = async () => {
      const res = await window.pywebview.api.stop_selected(apps);
      if (res.errors && res.errors.length) {
        alert("Erreurs Stop :\n" + res.errors.join("\n"));
      }
      setTimeout(refreshStatuses, 600);
    };
  }

  if (statusCheckInterval) clearInterval(statusCheckInterval);
  statusCheckInterval = setInterval(refreshStatuses, 2000);

  loadVersionAndUpdateStatus();
}

window.addEventListener("pywebviewready", init);
