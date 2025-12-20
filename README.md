# 🏁 iRacing Personal Launcher v1.2 - Package Complet

## 📦 Contenu

✅ **Fichiers sources :**
- `main.py` (VERSION 1.2 avec toutes les features)
- `updater.py` (Système de mise à jour automatique)
- `iRacing_Launcher.spec` (Config PyInstaller launcher)
- `updater.spec` (Config PyInstaller updater)

✅ **Interface utilisateur (dossier ui/) :**
- `index.html` (HTML avec affichage version)
- `script.js` (JS avec loadVersion() et restart)
- `style.css` (CSS COMPLET avec .restart-app et .status-indicator)
- `globals.css` (Styles globaux)

✅ **Documentation :**
- Ce README
- `.gitignore` (à créer)
- `build.bat` (script de build automatique)

---

## 🚀 Installation Ultra-Rapide

### Étape 1 : Extraction
Extrais tout le contenu dans un dossier (ex: `C:\launcher`)

### Étape 2 : Ajouter l'icône
Copie ton fichier `icone.ico` à la racine du dossier

### Étape 3 : Build automatique
Double-clique sur `build.bat`

OU en ligne de commande :
```bash
pyinstaller updater.spec
pyinstaller iRacing_Launcher.spec
copy dist\updater.exe dist\
```

### Étape 4 : Test
```bash
cd dist
.\iRacing_Launcher.exe
```

**Tu DOIS voir :**
- ✅ "Version 1.2" en bas à droite
- ✅ Cercle 🔴/🟢 de statut à côté de chaque app
- ✅ Bouton ⟳ orange pour restart

---

## ✨ Fonctionnalités v1.2

### 🎯 Nouvelles features
- ✅ **Bouton restart** (⟳) : Redémarre une app en un clic
- ✅ **Indicateur de statut** (🟢/🔴) : Voir si l'app tourne
- ✅ **Affichage version** : En bas à droite de l'interface
- ✅ **Mise à jour automatique** : Système complet avec updater

### 🔧 Features existantes
- ✅ Lancement multiple d'applications
- ✅ System tray avec minimisation
- ✅ Protection double instance
- ✅ Notification première fermeture
- ✅ Drag & drop pour réorganiser

---

## 📤 Publication sur GitHub

### 1. Initialiser Git (si pas déjà fait)
```bash
cd C:\launcher
git init
git remote add origin https://github.com/CoolBreeze06/iracing-launcher.git
```

### 2. Créer .gitignore
```
# Build files
build/
dist/
*.spec.backup

# Python
__pycache__/
*.py[cod]

# Application data
launcher_apps.json
launcher_settings.json
launcher.lock
*_backup.exe
```

### 3. Push sur GitHub
```bash
git add .
git commit -m "Version 1.2 - Complete with restart button and status indicators"
git push -u origin main --force
```

### 4. Créer la Release v1.2

1. Va sur https://github.com/CoolBreeze06/iracing-launcher/releases
2. **Create new release**
3. Tag : `v1.2`
4. Title : `iRacing Launcher v1.2`
5. Description :
   ```markdown
   ## 🎉 Version 1.2
   
   ### Nouveautés
   - ✅ Bouton restart (⟳) sur chaque application
   - ✅ Indicateur de statut temps réel (vert/rouge)
   - ✅ Affichage de la version dans l'interface
   - ✅ Système de mise à jour automatique complet
   
   ### Installation
   1. Téléchargez `iRacing_Launcher.exe`
   2. Lancez le fichier
   3. L'updater est inclus pour les futures mises à jour
   ```
6. **Upload** `dist\iRacing_Launcher.exe`
7. **Publish**

### 5. Mettre à jour version.json

Sur GitHub, édite ou crée `version.json` :
```json
{
  "version": "1.2",
  "download_url": "https://github.com/CoolBreeze06/iracing-launcher/releases/download/v1.2/iRacing_Launcher.exe",
  "changelog": "- Bouton restart fonctionnel\n- Indicateur de statut temps réel\n- Affichage version\n- Mise à jour automatique"
}
```

---

## 🧪 Test de mise à jour

Pour tester que le système de mise à jour fonctionne :

1. **Build la v1.2** (ce package)
2. **Upload sur GitHub** comme Release v1.2
3. **Modifie** `CURRENT_VERSION = "1.1"` dans main.py
4. **Rebuild** et teste
5. Le popup de mise à jour devrait apparaître !
6. Clique "Télécharger automatiquement"
7. L'app se met à jour vers v1.2 et redémarre

---

## 📋 Checklist avant publication

- [ ] Version changée à 1.2 dans `main.py`
- [ ] Console cachée (ShowWindow = 6) ligne ~88
- [ ] Icône `icone.ico` ajoutée
- [ ] Build réussi (`dist\iRacing_Launcher.exe` existe)
- [ ] Testé localement (version 1.2 visible)
- [ ] Bouton restart visible et fonctionnel
- [ ] Indicateur de statut fonctionne
- [ ] `updater.exe` copié dans dist/
- [ ] Release v1.2 créée sur GitHub
- [ ] `version.json` mis à jour
- [ ] Code source pushé sur GitHub

---

## 🆘 Problèmes courants

### "Le bouton restart n'apparaît pas"
→ Vérifie que `ui\style.css` contient bien `.restart-app`
→ Rebuild avec ce package

### "La version affichée est incorrecte"
→ Vérifie `CURRENT_VERSION` dans `main.py`
→ Rebuild

### "L'updater ne fonctionne pas"
→ Vérifie que `updater.exe` est à côté de `iRacing_Launcher.exe`
→ Vérifie l'URL dans `version.json`

### "L'app ne se ferme pas proprement"
→ Clic droit tray → Quitter
→ Dernière version de main.py avec quit_app() amélioré

---

## 🎯 Structure du package

```
iracing_launcher_v1.2/
├── main.py              (v1.2, tous les fixes)
├── updater.py           (système de mise à jour)
├── iRacing_Launcher.spec
├── updater.spec
├── build.bat            (compilation automatique)
├── README.md            (ce fichier)
├── icone.ico            (à ajouter)
└── ui/
    ├── index.html       (avec version display)
    ├── script.js        (avec loadVersion + restart)
    ├── style.css        (COMPLET avec restart + status)
    └── globals.css
```

---

## 🎊 C'est prêt !

Ce package contient **TOUT** ce qu'il faut pour avoir un launcher v1.2 100% fonctionnel.

Suis les étapes et tu auras :
- ✅ Un launcher professionnel
- ✅ Publié sur GitHub
- ✅ Avec système de mise à jour automatique
- ✅ Toutes les features qui marchent

**Bon build !** 🚀
