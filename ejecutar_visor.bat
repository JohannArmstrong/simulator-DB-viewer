@echo off
setlocal
title Lanzador - Simulator DB Viewer

cd /d "%~dp0"

where py >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se encontro el comando "py". Instala Python desde python.org.
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
)

if not exist "app.py" (
    echo [ERROR] No se encontro app.py en: %cd%
    pause
    exit /b 1
)

py -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Flask no esta instalado. Instalando...
    py -m pip install flask
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar Flask.
        pause
        exit /b 1
    )
) else (
    echo Flask ya esta instalado.
)

echo Iniciando servidor
start "Servidor Flask" cmd /k py app.py

echo Esperando a que el servidor termine de cargar
powershell -NoProfile -Command "$i=0; while($i -lt 120){ try{ $c=New-Object Net.Sockets.TcpClient; $c.Connect('127.0.0.1',5000); $c.Close(); exit 0 }catch{ Start-Sleep -Milliseconds 500; $i++ } }; exit 1"
if errorlevel 1 (
    echo [ERROR] El servidor no respondio a tiempo. Revisa la ventana "Servidor Flask".
    pause
    exit /b 1
)

start "" "http://127.0.0.1:5000"

exit /b 0
