@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set "CHECK_PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%CHECK_PYTHON%" set "CHECK_PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%CHECK_PYTHON%" goto missing_python
"%CHECK_PYTHON%" doctor_v2.py --hash
if errorlevel 1 goto failed
"%CHECK_PYTHON%" -m pytest fast_v2\tests -q
if errorlevel 1 goto failed
"%CHECK_PYTHON%" fast_v2\tray_app.py --self-test-ocr
if errorlevel 1 goto failed
echo V2 checks passed.
pause
exit /b 0
:missing_python
echo Python 3.12 is missing. See README.md.
:failed
echo V2 checks failed. See the output above.
pause
exit /b 1
