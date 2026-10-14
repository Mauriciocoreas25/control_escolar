@echo off
title SIGE Escolar - Aplicacion Movil Flutter
color 0A
echo ==============================================================
echo    INICIANDO APLICACION MOVIL DOCENTE (FLUTTER)
echo    Control Escolar - ITCA-FEPADE Megatec La Union
echo ==============================================================
echo.
echo Seleccione el modo de ejecucion:
echo   [1] Ejecutar en Navegador Chrome (Recomendado / Rapido)
echo   [2] Ejecutar en Aplicacion de Escritorio Windows
echo   [3] Ejecutar en Emulador Android (Pixel 4a)
echo.
set /p opcion="Ingrese opcion (1, 2 o 3) [Default 1]: "

if "%opcion%"=="" set opcion=1

cd /d "%~dp0app_movil"

if "%opcion%"=="1" (
    echo Iniciando Flutter en Google Chrome...
    C:\Users\jcore\flutter\bin\flutter.bat run -d chrome
) else if "%opcion%"=="2" (
    echo Iniciando Flutter para Windows...
    C:\Users\jcore\flutter\bin\flutter.bat run -d windows
) else if "%opcion%"=="3" (
    echo Iniciando en Emulador Android Pixel_4a...
    C:\Users\jcore\flutter\bin\flutter.bat emulators --launch Pixel_4a
    timeout /t 5 >nul
    C:\Users\jcore\flutter\bin\flutter.bat run
) else (
    echo Opcion invalida. Iniciando en Chrome por defecto...
    C:\Users\jcore\flutter\bin\flutter.bat run -d chrome
)
pause
