@echo off
echo ========================================
echo iRacing Launcher v1.2 - Build Script
echo ========================================
echo.

echo [1/4] Compilation de l'updater...
pyinstaller updater.spec
if %errorlevel% neq 0 (
    echo ERREUR: Compilation de l'updater echouee
    pause
    exit /b 1
)
echo.

echo [2/4] Compilation du launcher...
pyinstaller iRacing_Launcher.spec
if %errorlevel% neq 0 (
    echo ERREUR: Compilation du launcher echouee
    pause
    exit /b 1
)
echo.

echo [3/4] Copie de l'updater dans dist...
copy dist\updater.exe dist\ >nul 2>&1
echo.

echo [4/4] Verification...
if not exist "dist\iRacing_Launcher.exe" (
    echo ERREUR: iRacing_Launcher.exe introuvable
    pause
    exit /b 1
)
if not exist "dist\updater.exe" (
    echo ERREUR: updater.exe introuvable
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD v1.2 TERMINE AVEC SUCCES !
echo ========================================
echo.
echo Fichiers generes dans dist\ :
dir dist\*.exe
echo.
echo VERIFICATION :
echo - iRacing_Launcher.exe : OK
echo - updater.exe : OK
echo.
echo Pour tester : cd dist ^&^& iRacing_Launcher.exe
echo.
echo IMPORTANT : Verifiez que vous voyez :
echo  - "Version 1.2" en bas a droite
echo  - Bouton restart (symbole circulaire) sur chaque app
echo  - Cercle vert/rouge a cote de l'icone
echo.
pause
