@echo off
setlocal
set "DIRECTML_PYTHON=%~dp0.venv-directml\Scripts\python.exe"

if not exist "%DIRECTML_PYTHON%" (
    echo DirectML environment not found.
    echo Run this first from PowerShell:
    echo   powershell -ExecutionPolicy Bypass -File tools\setup_directml.ps1
    exit /b 2
)

"%DIRECTML_PYTHON%" "%~dp0tools\check_cuda_provider.py" --execution-provider directml --strict
if errorlevel 1 (
    echo DirectML provider validation failed. The app was not started with a silent CPU fallback.
    exit /b %errorlevel%
)

"%DIRECTML_PYTHON%" "%~dp0run.py" --execution-provider directml %*
