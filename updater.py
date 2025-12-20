"""
iRacing Launcher - Script de mise à jour automatique
Ce script remplace l'ancien launcher par la nouvelle version
"""
import os
import sys
import time
import shutil
import subprocess
import psutil

def wait_for_process_to_close(process_name, timeout=30):
    """Attend que le processus se ferme (max timeout secondes)"""
    print(f"Attente de la fermeture de {process_name}...")
    start_time = time.time()
    
    # Extraire juste le nom du fichier sans extension
    base_name = os.path.basename(process_name).replace('.exe', '').lower()
    
    while time.time() - start_time < timeout:
        found = False
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name']:
                    proc_name = proc.info['name'].replace('.exe', '').lower()
                    # Vérifier si le nom du processus correspond
                    if base_name in proc_name or proc_name in base_name:
                        found = True
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if not found:
            print(f"{process_name} fermé !")
            return True
        
        time.sleep(0.5)
    
    print(f"Timeout : {process_name} n'a pas fermé dans les {timeout} secondes")
    return False

def main():
    print("=" * 60)
    print("iRacing Launcher - Mise à jour automatique")
    print("=" * 60)
    
    # Récupérer les arguments
    if len(sys.argv) < 3:
        print("Erreur : Arguments manquants")
        print("Usage: updater.exe <nouveau_fichier> <ancien_fichier>")
        input("Appuyez sur Entrée pour quitter...")
        sys.exit(1)
    
    new_file = sys.argv[1]  # Le fichier téléchargé
    old_file = sys.argv[2]  # Le fichier à remplacer
    
    print(f"\nNouveau fichier : {new_file}")
    print(f"Ancien fichier : {old_file}")
    
    # Vérifier que les fichiers existent
    if not os.path.exists(new_file):
        print(f"\nErreur : Le nouveau fichier n'existe pas : {new_file}")
        input("Appuyez sur Entrée pour quitter...")
        sys.exit(1)
    
    if not os.path.exists(old_file):
        print(f"\nAvertissement : L'ancien fichier n'existe pas : {old_file}")
        print("Installation directe du nouveau fichier...")
    
    # Attendre que le launcher se ferme
    print("\n--- Étape 1/4 : Fermeture de l'ancien launcher ---")
    if not wait_for_process_to_close("iRacing_Launcher.exe", timeout=30):
        print("\nLe launcher ne s'est pas fermé automatiquement.")
        print("Veuillez fermer manuellement le launcher et appuyer sur Entrée...")
        input()
    
    # Petit délai de sécurité
    print("\nAttente de 2 secondes...")
    time.sleep(2)
    
    # Sauvegarder l'ancien fichier (backup)
    print("\n--- Étape 2/4 : Sauvegarde de l'ancienne version ---")
    if os.path.exists(old_file):
        backup_file = old_file.replace(".exe", "_backup.exe")
        try:
            if os.path.exists(backup_file):
                os.remove(backup_file)
            shutil.copy2(old_file, backup_file)
            print(f"Backup créé : {backup_file}")
        except Exception as e:
            print(f"Impossible de créer le backup : {e}")
            print("Continue quand même...")
    
    # Remplacer l'ancien fichier par le nouveau
    print("\n--- Étape 3/4 : Installation de la nouvelle version ---")
    try:
        if os.path.exists(old_file):
            os.remove(old_file)
            print(f"Ancien fichier supprimé")
        
        shutil.copy2(new_file, old_file)
        print(f"Nouveau fichier installé : {old_file}")
        
        # Supprimer le fichier téléchargé
        os.remove(new_file)
        print(f"Fichier temporaire supprimé : {new_file}")
        
    except Exception as e:
        print(f"\nErreur lors de l'installation : {e}")
        print("\nRestauration du backup...")
        if os.path.exists(backup_file):
            try:
                shutil.copy2(backup_file, old_file)
                print("Backup restauré avec succès")
            except Exception as e2:
                print(f"Impossible de restaurer le backup : {e2}")
        input("Appuyez sur Entrée pour quitter...")
        sys.exit(1)
    
    # Relancer le launcher
    print("\n--- Étape 4/4 : Redémarrage du launcher ---")
    
    # Supprimer le fichier lock s'il existe
    lock_file = os.path.join(os.path.dirname(old_file), "launcher.lock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            print(f"Fichier lock supprimé : {lock_file}")
        except Exception as e:
            print(f"Impossible de supprimer le lock : {e}")
    
    try:
        subprocess.Popen([old_file])
        print(f"Launcher redémarré : {old_file}")
    except Exception as e:
        print(f"Impossible de redémarrer le launcher : {e}")
        print(f"Veuillez lancer manuellement : {old_file}")
        input("Appuyez sur Entrée pour quitter...")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Mise à jour terminée avec succès !")
    print("=" * 60)
    print("\nFermeture automatique dans 3 secondes...")
    time.sleep(3)
    
    # Supprimer le script updater lui-même (optionnel)
    # Note: Ceci ne fonctionnera que si le script est un .exe standalone
    try:
        if getattr(sys, 'frozen', False):
            # On est dans un exe compilé, on peut essayer de se supprimer
            updater_path = sys.executable
            # Créer un script batch qui supprime l'updater après sa fermeture
            batch_script = f'''@echo off
timeout /t 2 /nobreak >nul
del "{updater_path}"
exit
'''
            batch_file = "cleanup_updater.bat"
            with open(batch_file, "w") as f:
                f.write(batch_script)
            
            subprocess.Popen(batch_file, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except:
        pass

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nErreur fatale : {e}")
        import traceback
        traceback.print_exc()
        input("\nAppuyez sur Entrée pour quitter...")
        sys.exit(1)
