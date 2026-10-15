@echo off
rem The imPress root console (v2.2): an interactive shell for operating the system as root.
rem   console.bat                     interactive
rem   console.bat -c "users list"     one command, then exit
cd /d "%~dp0backend" || exit /b 1
if not exist ".venv\Scripts\python.exe" (echo Not installed: run launcher.bat first & exit /b 1)
".venv\Scripts\python.exe" -m app.console %*
