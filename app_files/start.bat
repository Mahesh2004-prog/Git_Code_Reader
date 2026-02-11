@echo off
echo ==========================================
echo      Git Code Reader - Automated Setup
echo ==========================================

echo [1/6] Finding Python 3.12...
py -3.12 --version >nul 2>&1
if %errorlevel% equ 0 goto found_py_launcher

python --version >nul 2>&1
if %errorlevel% equ 0 goto found_python_default

echo ERROR: Python is not installed or not in PATH. Please install Python 3.10+
pause
exit /b

:found_py_launcher
echo Python 3.12 found (via py launcher).
set PYTHON_CMD=py -3.12
goto setup_venv

:found_python_default
echo Using default Python command.
set PYTHON_CMD=python
goto setup_venv

:setup_venv

echo.
echo [2/6] Setting up Virtual Environment (venv)...
if not exist venv (
    echo Creating venv...
    %PYTHON_CMD% -m venv venv
) else (
    echo venv already exists.
)

echo.
echo [3/6] Activating Virtual Environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b
)

echo.
echo [4/6] Installing Dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies. Please check your internet connection.
    pause
    exit /b
)

echo.
echo [5/6] Checking Ollama Model...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Ollama is not installed or not in PATH!
    echo You need Ollama running for AI features.
    echo Download it from https://ollama.com/
    echo.
) else (
    echo Ollama found. Checking for 'qwen2.5:3b' model...
    ollama list | findstr "qwen2.5:3b" >nul
    if %errorlevel% neq 0 (
        echo Model 'qwen2.5:3b' not found. Pulling it now...
        ollama pull qwen2.5:3b
    ) else (
        echo Model 'qwen2.5:3b' is ready.
    )
)

echo.
echo [6/6] Launching Application...
echo.
echo NOTE: If you see 'Connection refused' errors for localhost:8080, ignore them.
echo       The app is using local fallback mode for vector storage.
echo.
streamlit run app_files/app.py

pause
