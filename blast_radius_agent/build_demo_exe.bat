@echo off
setlocal
cd /d "%~dp0"

set "BUILD_VENV=.build-venv"
set "FALLBACK_VENV=.build-venv-%RANDOM%"

echo [1/4] Creating isolated build venv...
if exist "%BUILD_VENV%\Scripts\python.exe" (
  echo Existing venv found at %BUILD_VENV% - reusing it.
) else (
  python -m venv "%BUILD_VENV%"
  if errorlevel 1 (
    echo Primary venv path is unavailable ^(possibly locked^). Trying fallback path...
    set "BUILD_VENV=%FALLBACK_VENV%"
    python -m venv "%BUILD_VENV%"
    if errorlevel 1 (
      echo.
      echo Failed to create virtual environment. Ensure Python 3.10+ is installed and no process is locking this folder.
      exit /b 1
    )
  )
)

echo [2/4] Installing build dependencies in venv...
"%BUILD_VENV%\Scripts\python.exe" -m pip install --upgrade pip
"%BUILD_VENV%\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
  echo.
  echo Failed to install dependencies inside build venv.
  exit /b 1
)

echo [3/4] Building executable...
"%BUILD_VENV%\Scripts\python.exe" -m PyInstaller --noconfirm --onefile --name BlastRadiusDemo run.py
if errorlevel 1 (
  echo.
  echo Build failed.
  exit /b 1
)

echo [4/4] Done.
echo Executable: dist\BlastRadiusDemo.exe
echo.
echo Run it with:
echo   dist\BlastRadiusDemo.exe
