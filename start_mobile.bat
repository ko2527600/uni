@echo off
echo 📱 UniPortal Mobile Server Setup
echo ================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python first.
    pause
    exit /b 1
)

echo 🔧 Configuring mobile access...
python mobile_server.py

echo.
echo 🚀 Starting UniPortal server for mobile access...
echo.
echo ⚠️  IMPORTANT NOTES:
echo    - Your phone must be on the SAME WiFi network
echo    - Use the IP address shown above (not localhost)
echo    - For geolocation features, use HTTPS mode
echo.

set /p mode="Choose mode - (1) HTTP or (2) HTTPS: "

if "%mode%"=="2" (
    echo 🔒 Starting HTTPS server (for geolocation on mobile)...
    python run.py --https
) else (
    echo 🌐 Starting HTTP server...
    python run.py
)

pause