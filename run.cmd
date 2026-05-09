@echo off
setlocal EnableExtensions
set "SCRIPT_DIR=%~dp0"
set "RUNPY=%SCRIPT_DIR%run.py"

rem Prefer project venv, then python on PATH, then Python Launcher (py).
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%.venv\Scripts\python.exe" "%RUNPY%" %*
    exit /b %ERRORLEVEL%
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python "%RUNPY%" %*
    exit /b %ERRORLEVEL%
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py "%RUNPY%" %*
    exit /b %ERRORLEVEL%
)

echo Loi: Khong tim thay Python. Cai Python 3.9+ hoac tao .venv trong thu muc project.
exit /b 1
