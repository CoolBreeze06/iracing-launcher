"""
Updater SOLIDE
Args:
  updater.exe <nouveau_fichier> <ancien_fichier> <pid_optional> <new_version_optional>
"""
import os
import sys
import time
import shutil
import subprocess
import json
import psutil


def wait_for_pid(pid: int, timeout=30) -> bool:
    try:
        p = psutil.Process(pid)
    except Exception:
        return True

    start = time.time()
    while time.time() - start < timeout:
        try:
            if not p.is_running():
                return True
            p.status()
        except Exception:
            return True
        time.sleep(0.2)
    return False


def wait_until_file_is_free(path: str, timeout=60) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if not os.path.exists(path):
            return True
        try:
            tmp = path + ".locktest"
            os.rename(path, tmp)
            os.rename(tmp, path)
            return True
        except OSError:
            time.sleep(0.2)
    return False


def safe_remove(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass


def safe_rename(src: str, dst: str):
    safe_remove(dst)
    os.rename(src, dst)


def write_local_version(app_dir: str, version: str):
    try:
        out = {
            "version": version,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(os.path.join(app_dir, "version_local.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Impossible d'écrire version.json local: {e}")


def main():
    if len(sys.argv) < 3:
        print("Usage: updater.exe <nouveau_fichier> <ancien_fichier> <pid_optional> <new_version_optional>")
        input("Entrée pour quitter...")
        sys.exit(1)

    new_file = os.path.abspath(sys.argv[1])
    old_file = os.path.abspath(sys.argv[2])
    pid = int(sys.argv[3]) if len(sys.argv) >= 4 and sys.argv[3].isdigit() else None
    new_version = str(sys.argv[4]).strip() if len(sys.argv) >= 5 else ""

    app_dir = os.path.dirname(old_file)
    backup_file = old_file.replace(".exe", "_backup.exe")

    if not os.path.exists(new_file):
        print("❌ Le fichier téléchargé n'existe pas.")
        input("Entrée pour quitter...")
        sys.exit(1)

    # 1) attendre PID
    if pid is not None:
        ok = wait_for_pid(pid, timeout=30)
        if not ok:
            print("⚠️ PID pas terminé en 30s, on continue avec check lock fichier...")

    # 2) attendre libération fichier
    if os.path.exists(old_file):
        if not wait_until_file_is_free(old_file, timeout=60):
            print("❌ Fichier toujours verrouillé.")
            input("Ferme le launcher (tray inclus) puis Entrée...")
            sys.exit(1)

    # 3) backup + swap (rename, pas delete)
    try:
        safe_remove(backup_file)

        if os.path.exists(old_file):
            safe_rename(old_file, backup_file)

        try:
            safe_rename(new_file, old_file)
        except OSError:
            shutil.copy2(new_file, old_file)
            safe_remove(new_file)

        if new_version:
            write_local_version(app_dir, new_version)

    except Exception as e:
        print(f"❌ Erreur installation : {e}")
        if os.path.exists(backup_file):
            try:
                shutil.copy2(backup_file, old_file)
                print("✅ Backup restauré.")
            except Exception as e2:
                print(f"❌ Impossible de restaurer : {e2}")
        input("Entrée pour quitter...")
        sys.exit(1)

    # 4) relance
    lock_file = os.path.join(app_dir, "launcher.lock")
    safe_remove(lock_file)

    try:
        subprocess.Popen([old_file], cwd=app_dir, close_fds=True)
    except Exception as e:
        print(f"⚠️ Impossible de relancer automatiquement : {e}")
        print("Lance-le manuellement.")
        input("Entrée pour quitter...")


if __name__ == "__main__":
    main()
