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

# ===== VERSION =====
CURRENT_VERSION = "1.2"
UPDATE_CHECK_URL = "https://raw.githubusercontent.com/CoolBreeze06/iracing-launcher/main/version.json"

# ===== VÉRIFICATION INSTANCE UNIQUE =====
LOCK_FILE = "launcher.lock"

def check_single_instance():
    """
    Vérifie qu'une seule instance du launcher tourne.
    Si une autre instance existe, affiche un message et quitte.
    Retourne True si on peut continuer, False sinon.
    """
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
            
            # Vérifier si le processus existe encore
            if psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)
                    # Vérifier que c'est bien notre launcher
                    if "iRacing_Launcher" in proc.name() or "python" in proc.name().lower():
                        root = tk.Tk()
                        root.withdraw()
                        messagebox.showwarning(
                            "Application déjà lancée",
                            "L'iRacing Launcher est déjà en cours d'exécution.\n\n"
                            "Regardez dans la barre des tâches (system tray) pour l'icône 'L'."
                        )
                        root.destroy()
                        return False  # Ne pas continuer
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except:
            pass
    
    # Créer le fichier lock avec notre PID
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    
    return True  # OK pour continuer

def remove_lock():
    """Supprime le fichier lock à la fermeture"""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except:
        pass

# Vérifier l'instance unique au démarrage
if not check_single_instance():
    # Une autre instance existe déjà, on quitte
    sys.exit(0)

# ===== TOUT LE CODE PRINCIPAL DANS UN TRY/EXCEPT =====
try:
    # Chemin correct même en .exe onefile
    if getattr(sys, 'frozen', False):
        BASE_DIR = sys._MEIPASS
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    HTML_PATH = os.path.join(BASE_DIR, "ui", "index.html")
    APPS_FILE = "launcher_apps.json"
    SETTINGS_FILE = "launcher_settings.json"

    # Debug : ouvre une console pour voir les erreurs
    if getattr(sys, 'frozen', False):
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 6)  # cache la console

    print(f"HTML_PATH = {HTML_PATH}")
    print(f"Fichier existe ? {os.path.exists(HTML_PATH)}")

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
        """Charge les paramètres de l'application"""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_settings(settings):
        """Sauvegarde les paramètres de l'application"""
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

    # ===== SYSTÈME DE MISE À JOUR =====
    def check_for_updates():
        """
        Vérifie s'il y a une nouvelle version disponible.
        Retourne un dict avec les infos ou None si pas de mise à jour.
        """
        try:
            import urllib.request
            
            print("Vérification des mises à jour...")
            # Télécharger le fichier version.json depuis GitHub
            with urllib.request.urlopen(UPDATE_CHECK_URL, timeout=5) as response:
                data = json.loads(response.read().decode())
            
            latest_version = data.get("version", "")
            download_url = data.get("download_url", "")
            changelog = data.get("changelog", "")
            
            print(f"Version actuelle: {CURRENT_VERSION}, Dernière version: {latest_version}")
            
            # Comparer les versions (simple comparaison de string)
            if latest_version and latest_version != CURRENT_VERSION:
                print("Mise à jour disponible!")
                return {
                    "version": latest_version,
                    "download_url": download_url,
                    "changelog": changelog
                }
            
            print("Aucune mise à jour disponible")
            return None
            
        except Exception as e:
            print(f"Erreur vérification mise à jour: {e}")
            return None

    def download_update(download_url, progress_callback=None):
        """
        Télécharge la mise à jour dans le dossier Downloads.
        progress_callback: fonction appelée avec (bytes_downloaded, total_bytes)
        Retourne le chemin du fichier téléchargé ou None si erreur.
        """
        try:
            import urllib.request
            
            # Récupérer le dossier Downloads de l'utilisateur
            downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
            
            # Nom du fichier
            filename = os.path.basename(download_url)
            if not filename.endswith(".exe"):
                filename = "iRacing_Launcher_update.exe"
            
            filepath = os.path.join(downloads_folder, filename)
            
            # Télécharger avec progression
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
        """
        Affiche le dialog de mise à jour avec 2 options (VERSION BLOCKING).
        Retourne : "auto" (téléchargement auto), "github" (ouvrir GitHub), ou None (annuler)
        """
        root = tk.Tk()
        root.withdraw()
        
        message = (
            f"📢 Mise à jour disponible !\n\n"
            f"Version actuelle : {CURRENT_VERSION}\n"
            f"Nouvelle version : {update_info['version']}\n\n"
            f"Nouveautés :\n{update_info.get('changelog', 'Améliorations et corrections de bugs')}\n\n"
            f"Comment voulez-vous procéder ?"
        )
        
        # Créer une fenêtre personnalisée avec 3 boutons
        dialog = tk.Toplevel(root)
        dialog.title("Mise à jour disponible")
        dialog.geometry("500x350")
        dialog.resizable(False, False)
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (350 // 2)
        dialog.geometry(f"500x350+{x}+{y}")
        
        # Forcer la fenêtre au premier plan
        dialog.lift()
        dialog.attributes('-topmost', True)
        dialog.after_idle(dialog.attributes, '-topmost', False)
        
        result = {"choice": None}
        
        # Message
        label = tk.Label(dialog, text=message, justify=tk.LEFT, padx=20, pady=20, wraplength=460)
        label.pack(expand=True, fill=tk.BOTH)
        
        # Frame pour les boutons
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
        
        # Boutons
        btn_auto = tk.Button(button_frame, text="📥 Télécharger automatiquement", 
                             command=on_auto, width=25, height=2, bg="#4CAF50", fg="white")
        btn_auto.pack(pady=5)
        
        btn_github = tk.Button(button_frame, text="🔗 Ouvrir GitHub Release", 
                               command=on_github, width=25, height=2, bg="#2196F3", fg="white")
        btn_github.pack(pady=5)
        
        btn_later = tk.Button(button_frame, text="⏰ Plus tard", 
                              command=on_later, width=25, height=1)
        btn_later.pack(pady=5)
        
        dialog.protocol("WM_DELETE_WINDOW", on_later)
        
        # IMPORTANT : mainloop pour garder la fenêtre ouverte
        root.mainloop()
        
        choice = result["choice"]
        
        try:
            root.destroy()
        except:
            pass
        
        return choice

    def handle_update_check_blocking(update_info):
        """
        Gère tout le processus de vérification et mise à jour (VERSION BLOCKING).
        """
        print("handle_update_check() appelé")
        
        if not update_info:
            print("Pas de mise à jour")
            return
        
        print("Affichage du dialog...")
        choice = show_update_dialog_blocking(update_info)
        
        if choice == "github":
            # Ouvrir GitHub dans le navigateur
            import webbrowser
            release_url = update_info["download_url"].rsplit("/download/", 1)[0] if "/download/" in update_info["download_url"] else update_info["download_url"]
            webbrowser.open(release_url)
            
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(
                "GitHub ouvert",
                f"La page GitHub Release s'est ouverte dans votre navigateur.\n\n"
                f"Téléchargez le fichier .exe et remplacez l'ancien launcher."
            )
            root.destroy()
        
        elif choice == "auto":
            # Téléchargement automatique avec updater
            root = tk.Tk()
            root.withdraw()
            
            progress_window = tk.Toplevel(root)
            progress_window.title("Téléchargement en cours...")
            progress_window.geometry("400x150")
            progress_window.resizable(False, False)
            
            # Centrer
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (progress_window.winfo_screenheight() // 2) - (150 // 2)
            progress_window.geometry(f"400x150+{x}+{y}")
            
            status_label = tk.Label(progress_window, text="Téléchargement de la mise à jour...", pady=20)
            status_label.pack()
            
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
            
            download_thread = threading.Thread(target=do_download, daemon=True)
            download_thread.start()
            
            progress_window.mainloop()
            progress_window.destroy()
            
            if download_result["filepath"]:
                # Téléchargement réussi, lancer l'updater
                downloaded_file = download_result["filepath"]
                
                # Déterminer le chemin correct de l'exe actuel
                if getattr(sys, 'frozen', False):
                    # En mode exe compilé
                    current_exe = sys.executable
                else:
                    # En mode dev Python, construire le chemin vers le futur exe
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    current_exe = os.path.join(script_dir, "dist", "iRacing_Launcher.exe")
                
                print(f"Current exe: {current_exe}")
                print(f"Downloaded file: {downloaded_file}")
                
                # Chercher l'updater.exe
                if getattr(sys, 'frozen', False):
                    # En mode exe, l'updater devrait être dans le même dossier
                    updater_path = os.path.join(os.path.dirname(sys.executable), "updater.exe")
                else:
                    # En mode dev, chercher dans dist/ ou utiliser le script Python
                    updater_exe = os.path.join(os.path.dirname(__file__), "dist", "updater.exe")
                    if os.path.exists(updater_exe):
                        updater_path = updater_exe
                    else:
                        updater_path = os.path.join(os.path.dirname(__file__), "updater.py")
                
                print(f"Updater path: {updater_path}")
                
                if os.path.exists(updater_path):
                    try:
                        # Lancer l'updater
                        if updater_path.endswith('.py'):
                            # Mode dev
                            subprocess.Popen([sys.executable, updater_path, downloaded_file, current_exe])
                        else:
                            # Mode exe
                            subprocess.Popen([updater_path, downloaded_file, current_exe])
                        
                        # Quitter l'application pour permettre la mise à jour (sans popup supplémentaire)
                        root.destroy()
                        quit_app()
                        sys.exit(0)
                        
                    except Exception as e:
                        messagebox.showerror(
                            "Erreur de mise à jour",
                            f"Impossible de lancer le programme de mise à jour.\n\n"
                            f"Erreur : {e}\n\n"
                            f"Le fichier a été téléchargé dans :\n{downloaded_file}\n\n"
                            f"Vous pouvez remplacer manuellement l'ancien fichier."
                        )
                else:
                    # Pas d'updater, mode manuel
                    messagebox.showinfo(
                        "Téléchargement terminé",
                        f"La nouvelle version a été téléchargée dans :\n\n"
                        f"{downloaded_file}\n\n"
                        f"Pour installer la mise à jour :\n"
                        f"1. Fermez complètement cette application\n"
                        f"2. Remplacez l'ancien fichier par le nouveau\n"
                        f"3. Relancez l'application"
                    )
            else:
                messagebox.showerror(
                    "Erreur de téléchargement",
                    "Impossible de télécharger la mise à jour.\n\n"
                    "Veuillez réessayer plus tard ou télécharger manuellement depuis GitHub."
                )
            
            root.destroy()

    # Variable globale pour la fenêtre et l'icône
    window = None
    tray_icon = None

    def create_tray_image():
        """Crée une icône simple pour le system tray"""
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), 'white')
        dc = ImageDraw.Draw(image)
        
        dc.ellipse([8, 8, 56, 56], fill='#7bafbb', outline='#3aa0ff')
        dc.text((22, 16), "L", fill='white')
        
        return image

    def show_window(icon=None, item=None):
        """Affiche la fenêtre"""
        if window:
            window.show()

    def hide_window():
        """Cache la fenêtre dans le tray"""
        if window:
            window.hide()

    def quit_app(icon=None, item=None):
        """Quitte complètement l'application"""
        print("Fermeture complète de l'application...")
        remove_lock()
        
        # Arrêter le tray icon en premier
        if tray_icon:
            try:
                tray_icon.stop()
            except:
                pass
        
        # Détruire la fenêtre webview
        if window:
            try:
                window.destroy()
            except:
                pass
        
        # Attendre un peu que tout se termine
        time.sleep(0.5)
        
        # Forcer la fermeture du processus
        try:
            import signal
            os.kill(os.getpid(), signal.SIGTERM)
        except:
            pass
        
        # En dernier recours
        try:
            sys.exit(0)
        except:
            os._exit(0)

    def setup_tray():
        """Configure l'icône dans la barre des tâches"""
        global tray_icon
        
        image = create_tray_image()
        
        menu = Menu(
            MenuItem('Ouvrir', show_window, default=True),
            MenuItem('Quitter', quit_app)
        )
        
        tray_icon = Icon(
            "iRacing Launcher",
            image,
            "iRacing Personal Launcher",
            menu
        )
        
        threading.Thread(target=tray_icon.run, daemon=True).start()

    class Api:
        def get_apps(self): return load_apps()
        def save_apps(self, apps): save_apps(apps)
        def get_version(self): return CURRENT_VERSION

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
                import win32gui, win32ui, win32con
                from PIL import Image
                import base64
                from io import BytesIO

                large, _ = win32gui.ExtractIconEx(exe_path, 0)
                if not large: return None

                hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
                hbmp = win32ui.CreateBitmap()
                hbmp.CreateCompatibleBitmap(hdc, 32, 32)
                hdc2 = hdc.CreateCompatibleDC()
                hdc2.SelectObject(hbmp)
                hdc2.DrawIcon((0,0), large[0])
                win32gui.DestroyIcon(large[0])

                bmpstr = hbmp.GetBitmapBits(True)
                img = Image.frombuffer('RGBA', (32,32), bmpstr, 'raw', 'BGRA', 0, 1)

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
                for proc in psutil.process_iter(['name', 'exe']):
                    try:
                        if proc.info['name'] and proc.info['name'].lower() == exe_name:
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception as e:
                print(f"Erreur check_process_running: {e}")
            
            return False

        def get_all_process_statuses(self, apps):
            statuses = []
            for app in apps:
                is_running = self.check_process_running(app.get('path', ''))
                statuses.append(is_running)
            return statuses

        def restart_app(self, app_data):
            try:
                exe_path = app_data.get('path', '')
                if not exe_path or not os.path.exists(exe_path):
                    return {"ok": False, "error": "Chemin invalide"}
                
                exe_name = os.path.basename(exe_path).lower()
                killed = False
                
                for proc in psutil.process_iter(['name', 'exe']):
                    try:
                        if proc.info['name'] and proc.info['name'].lower() == exe_name:
                            proc.terminate()
                            killed = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if killed:
                    time.sleep(0.5)
                    
                    timeout = 3
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        if not self.check_process_running(exe_path):
                            break
                        time.sleep(0.1)
                
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
                    
                    for proc in psutil.process_iter(['name', 'exe']):
                        try:
                            if proc.info['name'] and proc.info['name'].lower() == exe_name.lower():
                                proc.terminate()
                                killed += 1
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                            
                except Exception as e:
                    errors.append(f"{app.get('name', 'Unknown')}: {str(e)}")
            
            psutil.wait_procs(psutil.process_iter(), timeout=3)
            
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

    # Configuration du system tray
    setup_tray()

    # ===== VÉRIFICATION DES MISES À JOUR AU DÉMARRAGE =====
    # Vérifier AVANT de créer la fenêtre webview
    print("Vérification des mises à jour...")
    update_info = check_for_updates()
    
    if update_info:
        print("Mise à jour trouvée, affichage du dialog...")
        handle_update_check_blocking(update_info)

    # Fonction appelée quand on clique sur la croix
    def on_closing():
        settings = load_settings()
        
        if not settings.get("hide_close_notification", False):
            root = tk.Tk()
            root.withdraw()
            result = messagebox.showinfo(
                "Application en veille",
                "L'application reste active dans la barre des tâches (system tray).\n\n"
                "Pour la rouvrir : double-clic sur l'icône 'L' dans la barre des tâches.\n"
                "Pour quitter complètement : clic droit sur l'icône → Quitter.",
                parent=root
            )
            root.destroy()
            
            settings["hide_close_notification"] = True
            save_settings(settings)
        
        hide_window()
        return False

    # Lancement
    print("Création de la fenêtre...")
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

    print("Démarrage de webview...")
    webview.start(debug=False, gui='edgehtml')

    # Nettoyer le lock file à la sortie
    remove_lock()

except Exception as e:
    error_msg = f"Erreur au démarrage:\n\n{str(e)}\n\n{traceback.format_exc()}"
    print(error_msg)
    
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Erreur fatale", error_msg)
    root.destroy()
    
    remove_lock()
    input("Appuyez sur Entrée pour quitter...")
    sys.exit(1)
