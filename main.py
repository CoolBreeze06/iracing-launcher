import webview
import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import threading
import psutil
import time
import traceback

UPDATE_CHECK_URL = "https://raw.githubusercontent.com/CoolBreeze06/iracing-launcher/main/version.json"


def is_frozen():
    return getattr(sys, "frozen", False)


# ===== CHEMINS =====
if is_frozen():
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
    RESOURCE_DIR = sys._MEIPASS
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = APP_DIR

HTML_PATH = os.path.join(RESOURCE_DIR, "ui", "index.html")
APPS_FILE = os.path.join(APP_DIR, "launcher_apps.json")
SETTINGS_FILE = os.path.join(APP_DIR, "launcher_settings.json")
LOCK_FILE = os.path.join(APP_DIR, "launcher.lock")

# Version locale dans le dossier de l'app
LOCAL_VERSION_FILE = os.path.join(APP_DIR, "version_local.json")
DEFAULT_VERSION = "1.0"


def load_local_version() -> str:
    try:
        if os.path.exists(LOCAL_VERSION_FILE):
            with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                v = str(data.get("version", "")).strip()
                if v:
                    return v
    except:
        pass

    # Si absent/cassé -> recrée en 1.0
    try:
        with open(LOCAL_VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"version": DEFAULT_VERSION}, f, indent=2, ensure_ascii=False)
    except:
        pass

    return DEFAULT_VERSION


def check_single_instance():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r", encoding="utf-8") as f:
                pid = int(f.read().strip())

            if psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)
                    if proc.is_running():
                        root = tk.Tk()
                        root.withdraw()
                        messagebox.showwarning(
                            "Application déjà lancée",
                            "L'iRacing Launcher est déjà en cours d'exécution.\n\n"
                            "Regardez dans la barre des tâches (system tray) pour l'icône 'L'."
                        )
                        root.destroy()
                        return False
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except:
            pass

    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
    return True


def remove_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass


if not check_single_instance():
    sys.exit(0)


try:
    # cache console en exe
    if is_frozen():
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 6)

    if not os.path.exists(HTML_PATH):
        raise FileNotFoundError(f"index.html introuvable ! Chemin : {HTML_PATH}")

    def load_apps():
        if os.path.exists(APPS_FILE):
            try:
                with open(APPS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_apps(apps):
        with open(APPS_FILE, "w", encoding="utf-8") as f:
            json.dump(apps, f, indent=4, ensure_ascii=False)

    def load_settings():
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_settings(settings):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

    # ===== UPDATE =====
    def fetch_remote_version():
        """Retourne (latest_version, download_url, changelog) ou lève exception."""
        import urllib.request
        with urllib.request.urlopen(UPDATE_CHECK_URL, timeout=6) as response:
            data = json.loads(response.read().decode())
        latest_version = str(data.get("version", "")).strip()
        download_url = str(data.get("download_url", "")).strip()
        changelog = str(data.get("changelog", "")).strip()
        return latest_version, download_url, changelog

    def check_for_updates():
        """Retourne dict si MAJ dispo, sinon None."""
        try:
            current = load_local_version()
            latest_version, download_url, changelog = fetch_remote_version()

            if latest_version and latest_version != current:
                return {"version": latest_version, "download_url": download_url, "changelog": changelog}

            return None
        except Exception as e:
            print(f"Erreur vérification mise à jour: {e}")
            return None

    def download_update(download_url, progress_callback=None):
        try:
            import urllib.request

            downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads_folder, exist_ok=True)

            filename = os.path.basename(download_url)
            if not filename.lower().endswith(".exe"):
                filename = "iRacing_Launcher_update.exe"

            filepath = os.path.join(downloads_folder, filename)

            def report_progress(block_num, block_size, total_size):
                if progress_callback:
                    downloaded = block_num * block_size
                    progress_callback(downloaded, total_size)

            urllib.request.urlretrieve(download_url, filepath, reporthook=report_progress)
            return filepath

        except Exception as e:
            print(f"Erreur téléchargement: {e}")
            return None

    def show_update_dialog_blocking(update_info):
        root = tk.Tk()
        root.withdraw()

        current = load_local_version()
        message = (
            f"📢 Mise à jour disponible !\n\n"
            f"Version actuelle : {current}\n"
            f"Nouvelle version : {update_info['version']}\n\n"
            f"Nouveautés :\n{update_info.get('changelog', 'Améliorations et corrections de bugs')}\n\n"
            f"Comment voulez-vous procéder ?"
        )

        dialog = tk.Toplevel(root)
        dialog.title("Mise à jour disponible")
        dialog.geometry("500x350")
        dialog.resizable(False, False)

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (350 // 2)
        dialog.geometry(f"500x350+{x}+{y}")

        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.after_idle(dialog.attributes, "-topmost", False)

        result = {"choice": None}

        label = tk.Label(dialog, text=message, justify=tk.LEFT, padx=20, pady=20, wraplength=460)
        label.pack(expand=True, fill=tk.BOTH)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        def on_auto():
            result["choice"] = "auto"
            dialog.destroy()
            root.quit()

        def on_github():
            result["choice"] = "github"
            dialog.destroy()
            root.quit()

        def on_later():
            result["choice"] = None
            dialog.destroy()
            root.quit()

        tk.Button(button_frame, text="📥 Télécharger automatiquement",
                  command=on_auto, width=25, height=2, bg="#4CAF50", fg="white").pack(pady=5)

        tk.Button(button_frame, text="🔗 Ouvrir GitHub Release",
                  command=on_github, width=25, height=2, bg="#2196F3", fg="white").pack(pady=5)

        tk.Button(button_frame, text="⏰ Plus tard",
                  command=on_later, width=25, height=1).pack(pady=5)

        dialog.protocol("WM_DELETE_WINDOW", on_later)
        root.mainloop()

        choice = result["choice"]
        try:
            root.destroy()
        except:
            pass
        return choice

    window = None
    tray_icon = None

    def create_tray_image():
        width = 64
        height = 64
        image = Image.new("RGB", (width, height), "white")
        dc = ImageDraw.Draw(image)
        dc.ellipse([8, 8, 56, 56], fill="#7bafbb", outline="#3aa0ff")
        dc.text((22, 16), "L", fill="white")
        return image

    def show_window(icon=None, item=None):
        if window:
            window.show()

    def hide_window():
        if window:
            window.hide()

    def quit_app(icon=None, item=None):
        remove_lock()

        if tray_icon:
            try:
                tray_icon.stop()
            except:
                pass

        if window:
            try:
                window.destroy()
            except:
                pass

        time.sleep(0.3)
        try:
            sys.exit(0)
        except:
            os._exit(0)

    def setup_tray():
        global tray_icon
        image = create_tray_image()
        menu = Menu(
            MenuItem("Ouvrir", show_window, default=True),
            MenuItem("Quitter", quit_app)
        )
        tray_icon = Icon("iRacing Launcher", image, "iRacing Personal Launcher", menu)
        threading.Thread(target=tray_icon.run, daemon=True).start()

    def launch_updater(downloaded_file: str, latest_version: str):
        current_exe = os.path.abspath(sys.executable) if is_frozen() else os.path.join(APP_DIR, "dist", "iRacing_Launcher.exe")
        current_pid = str(os.getpid())

        updater_exe = os.path.join(APP_DIR, "updater.exe")
        updater_py = os.path.join(APP_DIR, "Updater.py")

        if os.path.exists(updater_exe):
            cmd = [updater_exe, downloaded_file, current_exe, current_pid, latest_version]
        else:
            cmd = [sys.executable, updater_py, downloaded_file, current_exe, current_pid, latest_version]

        subprocess.Popen(cmd, cwd=APP_DIR, close_fds=True)

        # Quit fort => libère le .exe vite (anti-lock)
        try:
            quit_app()
        finally:
            os._exit(0)

    def handle_update_check_blocking(update_info):
        if not update_info:
            return

        choice = show_update_dialog_blocking(update_info)

        if choice == "github":
            import webbrowser
            release_url = update_info["download_url"].rsplit("/download/", 1)[0] if "/download/" in update_info["download_url"] else update_info["download_url"]
            webbrowser.open(release_url)

            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(
                "GitHub ouvert",
                "La page GitHub Release s'est ouverte.\n\nTélécharge le .exe et remplace l'ancien."
            )
            root.destroy()

        elif choice == "auto":
            root = tk.Tk()
            root.withdraw()

            progress_window = tk.Toplevel(root)
            progress_window.title("Téléchargement en cours...")
            progress_window.geometry("400x150")
            progress_window.resizable(False, False)

            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (progress_window.winfo_screenheight() // 2) - (150 // 2)
            progress_window.geometry(f"400x150+{x}+{y}")

            tk.Label(progress_window, text="Téléchargement de la mise à jour...", pady=20).pack()

            progress_bar = tk.Canvas(progress_window, width=360, height=30, bg="white", highlightthickness=1)
            progress_bar.pack(pady=10)

            progress_text = tk.Label(progress_window, text="0%")
            progress_text.pack()

            download_result = {"filepath": None}

            def update_progress(downloaded, total):
                if total > 0:
                    percent = int((downloaded / total) * 100)
                    progress_text.config(text=f"{percent}% ({downloaded // 1024} KB / {total // 1024} KB)")
                    progress_bar.delete("all")
                    bar_width = int((downloaded / total) * 360)
                    progress_bar.create_rectangle(0, 0, bar_width, 30, fill="#4CAF50", outline="")

            def do_download():
                filepath = download_update(update_info["download_url"], update_progress)
                download_result["filepath"] = filepath
                progress_window.quit()

            threading.Thread(target=do_download, daemon=True).start()
            progress_window.mainloop()
            progress_window.destroy()

            if download_result["filepath"]:
                downloaded_file = download_result["filepath"]
                root.destroy()
                launch_updater(downloaded_file, update_info["version"])
            else:
                messagebox.showerror("Erreur", "Téléchargement impossible.")
                root.destroy()

    class Api:
        def get_apps(self): return load_apps()
        def save_apps(self, apps): save_apps(apps)

        def get_version(self):
            return load_local_version()

        def get_update_status(self):
            """
            Pour l'UI (badge): donne latest version + ok/erreur
            """
            try:
                current = load_local_version()
                latest, _, _ = fetch_remote_version()
                if not latest:
                    return {"ok": True, "latest": current}
                return {"ok": True, "latest": latest}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        def browse_exe(self):
            root = tk.Tk()
            root.withdraw()
            file = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
            root.destroy()
            return file or ""

        def ask_yes_no(self, title, message):
            root = tk.Tk()
            root.withdraw()
            res = messagebox.askyesno(title, message)
            root.destroy()
            return res

        def get_icon(self, exe_path):
            if not exe_path or not os.path.exists(exe_path):
                return None
            try:
                import win32gui, win32ui
                from PIL import Image
                import base64
                from io import BytesIO

                large, _ = win32gui.ExtractIconEx(exe_path, 0)
                if not large:
                    return None

                hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
                hbmp = win32ui.CreateBitmap()
                hbmp.CreateCompatibleBitmap(hdc, 32, 32)
                hdc2 = hdc.CreateCompatibleDC()
                hdc2.SelectObject(hbmp)
                hdc2.DrawIcon((0, 0), large[0])
                win32gui.DestroyIcon(large[0])

                bmpstr = hbmp.GetBitmapBits(True)
                img = Image.frombuffer("RGBA", (32, 32), bmpstr, "raw", "BGRA", 0, 1)

                buffered = BytesIO()
                img.save(buffered, format="PNG")
                return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()
            except Exception as e:
                print("Erreur icône :", e)
                return None

        def check_process_running(self, exe_path):
            if not exe_path or not os.path.exists(exe_path):
                return False
            exe_name = os.path.basename(exe_path).lower()
            try:
                for proc in psutil.process_iter(["name", "exe"]):
                    try:
                        if proc.info["name"] and proc.info["name"].lower() == exe_name:
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception as e:
                print(f"Erreur check_process_running: {e}")
            return False

        def get_all_process_statuses(self, apps):
            statuses = []
            for app in apps:
                statuses.append(self.check_process_running(app.get("path", "")))
            return statuses

        def restart_app(self, app_data):
            try:
                exe_path = app_data.get("path", "")
                if not exe_path or not os.path.exists(exe_path):
                    return {"ok": False, "error": "Chemin invalide"}

                exe_name = os.path.basename(exe_path).lower()
                killed = False

                for proc in psutil.process_iter(["name", "exe"]):
                    try:
                        if proc.info["name"] and proc.info["name"].lower() == exe_name:
                            proc.terminate()
                            killed = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                if killed:
                    time.sleep(0.5)

                if app_data.get("admin_required"):
                    subprocess.Popen(f'powershell -Command "Start-Process \'{exe_path}\' -Verb RunAs"', shell=True)
                else:
                    subprocess.Popen(exe_path)

                return {"ok": True, "was_running": killed}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        def start_selected(self, apps):
            errors = []
            for app in [a for a in apps if a.get("checked")]:
                try:
                    if app.get("admin_required"):
                        subprocess.Popen(f'powershell -Command "Start-Process \'{app["path"]}\' -Verb RunAs"', shell=True)
                    else:
                        subprocess.Popen(app["path"])
                except Exception as e:
                    errors.append(str(e))
            return {"ok": not errors, "errors": errors}

        def stop_selected(self, apps):
            killed = 0
            errors = []
            for app in [a for a in apps if a.get("checked")]:
                try:
                    exe_name = os.path.basename(app["path"])
                    for proc in psutil.process_iter(["name", "exe"]):
                        try:
                            if proc.info["name"] and proc.info["name"].lower() == exe_name.lower():
                                proc.terminate()
                                killed += 1
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except Exception as e:
                    errors.append(f"{app.get('name', 'Unknown')}: {str(e)}")
            return {"killed": killed, "errors": errors}

        def move_app_up(self, index):
            apps = load_apps()
            if index > 0:
                apps[index], apps[index - 1] = apps[index - 1], apps[index]
                save_apps(apps)
            return True

        def move_app_down(self, index):
            apps = load_apps()
            if index < len(apps) - 1:
                apps[index], apps[index + 1] = apps[index + 1], apps[index]
                save_apps(apps)
            return True

        def resize_window(self, w, h):
            window.resize(w, h)

        def minimize_to_tray(self):
            hide_window()

    setup_tray()

    # popup MAJ au démarrage (ton choix, tu peux laisser)
    update_info = check_for_updates()
    if update_info:
        handle_update_check_blocking(update_info)

    def on_closing():
        settings = load_settings()
        if not settings.get("hide_close_notification", False):
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(
                "Application en veille",
                "L'application reste active dans la barre des tâches (system tray).\n\n"
                "Pour la rouvrir : double-clic sur l'icône 'L'.\n"
                "Pour quitter complètement : clic droit sur l'icône → Quitter.",
                parent=root
            )
            root.destroy()
            settings["hide_close_notification"] = True
            save_settings(settings)

        hide_window()
        return False

    window = webview.create_window(
        "iRacing Personal Launcher",
        HTML_PATH,
        js_api=Api(),
        width=1040,
        height=840,
        resizable=True,
        min_size=(900, 700),
        on_top=False
    )

    window.events.closing += on_closing
    webview.start(debug=False, gui="edgehtml")

    remove_lock()

except Exception as e:
    error_msg = f"Erreur au démarrage:\n\n{str(e)}\n\n{traceback.format_exc()}"
    print(error_msg)

    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Erreur fatale", error_msg)
    root.destroy()

    remove_lock()
    sys.exit(1)
