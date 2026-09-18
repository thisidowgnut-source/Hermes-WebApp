@echo off
echo Mengaktifkan Auto-Start untuk Hermes WebApp...

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SOURCE_FILE=%~dp0hermes_startup.vbs"

if not exist "%SOURCE_FILE%" (
    echo [ERROR] hermes_startup.vbs tidak dijumpai!
    pause
    exit /b
)

copy /Y "%SOURCE_FILE%" "%STARTUP_FOLDER%\"
echo.
echo [BERJAYA] Hermes WebApp akan Auto-Start secara senyap (stealth mode) setiap kali PC dihidupkan!
echo.
echo [AUTO-HEALING AKTIF] URL WebApp di dalam Telegram akan dikemaskini secara automatik (Self-Healing) tanpa sebarang campur tangan manual!
pause
