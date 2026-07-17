@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo [1/6] Creating Python 3.11 build environment...
py -3.11 -m venv --clear .venv
if errorlevel 1 goto :error
call .venv\Scripts\activate.bat
if errorlevel 1 goto :error

echo [2/6] Installing pinned build dependencies...
python -m pip install --disable-pip-version-check -r requirements-build.txt
if errorlevel 1 goto :error
python -m pip install --disable-pip-version-check --no-deps -e .
if errorlevel 1 goto :error

echo [3/6] Running tests...
python -m pytest -q
if errorlevel 1 goto :error

echo [4/6] Building DeviceReport.exe...
python -m PyInstaller DeviceReport.spec --clean --noconfirm
if errorlevel 1 goto :error

echo [5/6] Verifying exactly one file in dist...
if not exist "dist\DeviceReport.exe" (
    echo ERROR: dist\DeviceReport.exe was not created.
    goto :error
)
for /f %%C in ('dir /b /a-d "dist" ^| find /c /v ""') do set "FILE_COUNT=%%C"
if not "%FILE_COUNT%"=="1" (
    echo ERROR: dist must contain exactly one file, found %FILE_COUNT%.
    goto :error
)

echo [6/6] Build completed successfully.
echo Result: %CD%\dist\DeviceReport.exe
exit /b 0

:error
echo Build failed.
exit /b 1

