@echo off
title Sistema de Control Escolar - Lanzador
color 0B
echo ==============================================================
echo    INICIANDO SISTEMA DE CONTROL ESCOLAR Y REGISTRO ACADEMICO
echo    ITCA-FEPADE Megatec La Union
echo ==============================================================
echo.
echo [1/3] Verificando Base de Datos MySQL...
echo Asegurate de que Laragon este abierto con MySQL iniciado (Puerto 3306).
echo.
echo [2/3] Levantando API REST Central (FastAPI en Puerto 8001)...
start "API REST - FastAPI (Puerto 8001)" cmd /k "cd /d %~dp0backend && .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

echo [3/3] Levantando Portal Web Administrativo (Django en Puerto 8080)...
start "Portal Web - Django (Puerto 8080)" cmd /k "cd /d %~dp0frontend_web && ..\backend\venv\Scripts\python.exe manage.py runserver 8080"

timeout /t 3 >nul
echo.
echo ==============================================================
echo    SISTEMA LISTO PARA LA DEMOSTRACION!
echo.
echo    - Portal Web:   http://127.0.0.1:8080/login/
echo    - API Swagger:  http://127.0.0.1:8001/docs
echo.
echo    Abriendo navegador automaticamente...
echo ==============================================================
start http://127.0.0.1:8080/login/
exit
