let apps = [];
let statusCheckInterval = null;

function el(tag, className) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  return e;
}
function $(id) { return document.getElementById(id); }

async function saveApps() {
  await window.pywebview.api.save_apps(apps);
}

async function autoResizeWindow() {
  try {
    const frame = document.querySelector(".frame");
    if (!frame) return;
    const r = frame.getBoundingClientRect();
    const wantedWidth = 1024;
    const wantedHeight = Math.max(820, Math.ceil(r.height + 40));
    await window.pywebview.api.resize_window(wantedWidth, wantedHeight);
  } catch (e) {
    console.error(e);
  }
}

async function updateProcessStatuses() {
  /**
   * Met à jour les indicateurs de statut pour toutes les apps
   * Appelé périodiquement toutes les 2 secondes
   */
  try {
    const statuses = await window.pywebview.api.get_all_process_statuses(apps);
    
    statuses.forEach((isRunning, idx) => {
      const statusIndicator = document.querySelector(`[data-app-index="${idx}"] .status-indicator`);
      if (statusIndicator) {
        statusIndicator.classList.toggle('running', isRunning);
        statusIndicator.classList.toggle('stopped', !isRunning);
      }
    });
  } catch (e) {
    console.error("Erreur updateProcessStatuses:", e);
  }
}

function render() {
  const list = $("appsList");
  if (!list) return;
  list.innerHTML = "";

  apps.forEach((a, idx) => {
    const row = el("div", "app-row");
    row.setAttribute('data-app-index', idx);  // Pour identifier la row lors de l'update des statuts

    const check = el("div", "case-coche");
    if (a.checked) check.classList.add("checked");
    check.onclick = async () => {
      a.checked = !a.checked;
      check.classList.toggle("checked", a.checked);
      await saveApps();
    };

    // 🟢 NOUVEAU : Indicateur de statut
    const statusIndicator = el("div", "status-indicator");
    statusIndicator.classList.add('stopped'); // Par défaut: arrêté
    statusIndicator.title = "Status du processus";

    const icon = el("div", "icone");
    if (a.icon) icon.style.backgroundImage = `url(${a.icon})`;

    const name = el("div", "name-apps");
    name.textContent = a.name || "App";

    const path = el("div", "file-path");
    path.textContent = a.path || "";

    const browse = el("div", "search-apps");
    browse.onclick = async () => {
      const p = await window.pywebview.api.browse_exe();
      if (p) {
        a.path = p;
        a.icon = await window.pywebview.api.get_icon(p);
        await saveApps();
        render();
      }
    };

    // ⟳ NOUVEAU : Bouton Restart
    const restart = el("div", "restart-app");
    restart.title = "Redémarrer l'application";
    restart.onclick = async () => {
      // Confirmation optionnelle
      if (!confirm(`Redémarrer ${a.name || "cette app"} ?`)) return;
      
      // Désactiver le bouton pendant l'opération
      restart.style.opacity = "0.5";
      restart.style.pointerEvents = "none";
      
      try {
        const result = await window.pywebview.api.restart_app(a);
        
        if (result.ok) {
          // Petit feedback visuel
          restart.style.backgroundColor = "#6fb15e";
          setTimeout(() => {
            restart.style.backgroundColor = "";
          }, 1000);
          
          // Mettre à jour immédiatement le statut
          setTimeout(updateProcessStatuses, 500);
        } else {
          alert(`Erreur lors du redémarrage:\n${result.error || 'Erreur inconnue'}`);
        }
      } catch (e) {
        alert(`Erreur: ${e}`);
      } finally {
        // Réactiver le bouton
        restart.style.opacity = "1";
        restart.style.pointerEvents = "auto";
      }
    };

    // Bouton monter ⬆️
    const moveUp = el("div", "move-up");
    moveUp.onclick = async () => {
      if (idx > 0) {
        await window.pywebview.api.move_app_up(idx);
        await loadApps();
      }
    };
    if (idx === 0) moveUp.style.opacity = "0.3";

    // Bouton descendre ⬇️
    const moveDown = el("div", "move-down");
    moveDown.onclick = async () => {
      if (idx < apps.length - 1) {
        await window.pywebview.api.move_app_down(idx);
        await loadApps();
      }
    };
    if (idx === apps.length - 1) moveDown.style.opacity = "0.3";

    const del = el("div", "delete-apps");
    del.onclick = async () => {
      if (confirm(`Supprimer ${a.name || "cette app"} ?`)) {
        apps.splice(idx, 1);
        await saveApps();
        render();
        autoResizeWindow();
      }
    };

    // ✅ ORDRE MODIFIÉ: status après checkbox, restart avant move-up
    row.append(check, statusIndicator, icon, name, path, browse, restart, moveUp, moveDown, del);
    list.appendChild(row);
  });

  autoResizeWindow();
  
  // Mettre à jour les statuts immédiatement après le render
  setTimeout(updateProcessStatuses, 100);
}

async function loadApps() {
  apps = await window.pywebview.api.get_apps();
  apps.forEach(a => {
    if (typeof a.checked === "undefined") a.checked = true;
    if (typeof a.admin_required === "undefined") a.admin_required = false;
  });
  render();
}

function startStatusMonitoring() {
  /**
   * Démarre le monitoring des processus toutes les 2 secondes
   */
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval);
  }
  
  statusCheckInterval = setInterval(updateProcessStatuses, 2000);
}

function stopStatusMonitoring() {
  /**
   * Arrête le monitoring (optionnel, utile si on veut économiser les ressources)
   */
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval);
    statusCheckInterval = null;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const btnAdd = $("btnAdd");
  const btnStart = $("btnStart");
  const btnStop = $("btnStop");

  if (btnAdd) {
    btnAdd.onclick = async () => {
      const p = await window.pywebview.api.browse_exe();
      if (!p) return;

      const defaultName = p.split("\\").pop().replace(".exe", "");
      const name = prompt("Nom de l'application :", defaultName);
      if (!name) return;

      const admin_required = await window.pywebview.api.ask_yes_no(
        "Droits administrateur",
        "Lancer cette application en administrateur ?"
      );

      const icon = await window.pywebview.api.get_icon(p);

      apps.push({
        name: name,
        path: p,
        icon: icon,
        admin_required: admin_required,
        checked: true
      });

      await saveApps();
      await loadApps();
    };
  }

  if (btnStart) {
    btnStart.onclick = async () => {
      const res = await window.pywebview.api.start_selected(apps);
      if (res.errors?.length) alert("Erreurs :\n" + res.errors.join("\n"));
      
      // Mettre à jour les statuts après le lancement
      setTimeout(updateProcessStatuses, 1000);
    };
  }

  if (btnStop) {
    btnStop.onclick = async () => {
      const res = await window.pywebview.api.stop_selected(apps);
      if (res.errors?.length) {
        alert(`${res.killed} processus fermés\n\nErreurs :\n` + res.errors.join("\n"));
      } else {
        alert(`${res.killed} processus fermés`);
      }
      
      // Mettre à jour les statuts après l'arrêt
      setTimeout(updateProcessStatuses, 500);
    };
  }
});

window.addEventListener("pywebviewready", async () => {
  await loadApps();
  setTimeout(autoResizeWindow, 100);
  
  // Démarrer le monitoring des processus
  startStatusMonitoring();
});

window.addEventListener("resize", () => setTimeout(autoResizeWindow, 100));

// Nettoyer l'interval quand la fenêtre se ferme (optionnel)
window.addEventListener("beforeunload", () => {
  stopStatusMonitoring();
});