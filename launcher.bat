@echo off
rem imPress launcher for Windows: everything from a fresh checkout to a running
rem server, without Docker. Safe to run every time (double-click or from cmd).
rem
rem   launcher.bat                          http://127.0.0.1:8000, this computer only
rem   set IMPRESS_HOST=0.0.0.0 ^& launcher.bat   reachable by classroom gateways
rem   set IMPRESS_PORT=9000 ^& launcher.bat
rem
rem 1. finds Python 3.12+ (installs it with winget when missing)
rem 2. creates backend\.venv and installs the dependencies (pip skips what is there)
rem 3. creates backend\.env with fresh secrets if it does not exist (keeps existing values)
rem 4. frees the port: stops whatever is listening on it
rem 5. starts the server
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "ROOT=%CD%"
set "BACKEND=%ROOT%\backend"
if not defined IMPRESS_HOST set "IMPRESS_HOST=127.0.0.1"
if not defined IMPRESS_PORT set "IMPRESS_PORT=8000"
set "VPY=%BACKEND%\.venv\Scripts\python.exe"
set "CHECK=import sys, venv, ensurepip; sys.exit(0 if sys.version_info >= (3, 12) else 1)"

rem ---- 1. Python -----------------------------------------------------------
echo ==^> Python 3.12 or newer
call :find_python
if not defined PY (
  where winget >nul 2>&1 || (
    echo Error: Python 3.12+ is missing and winget is not available. Install Python from
    echo https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^), then run this again.
    goto :fail
  )
  echo ==^> Installing Python 3.12 with winget
  winget install --exact --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
  rem winget does not update this window's PATH: look in the usual install folder too
  if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%PATH%"
  call :find_python
  if not defined PY (
    echo Error: Python was installed but is not found yet. Close this window and run launcher.bat again.
    goto :fail
  )
)
for /f "delims=" %%v in ('%PY% --version 2^>^&1') do echo     %%v

rem ---- 2. virtualenv and dependencies --------------------------------------
if exist "%VPY%" (
  "%VPY%" -c "%CHECK%" >nul 2>&1 || (
    echo ==^> backend\.venv is broken or too old: recreating it
    rmdir /s /q "%BACKEND%\.venv"
  )
)
if not exist "%VPY%" (
  echo ==^> Creating backend\.venv
  %PY% -m venv "%BACKEND%\.venv" || goto :fail
  "%VPY%" -m pip install --quiet --upgrade pip
)
echo ==^> Dependencies
"%VPY%" -m pip install --quiet --disable-pip-version-check -r "%BACKEND%\requirements.txt" || goto :fail

rem ---- 3. configuration ----------------------------------------------------
echo ==^> Configuration (backend\.env)
"%VPY%" "%ROOT%\scripts\init_env.py" "%BACKEND%" || goto :fail
pushd "%BACKEND%"
"%VPY%" -c "from app.main import app; print(f'    imPress {app.version}')"
if errorlevel 1 ( popd & echo Error: the app does not import; see the error above. & goto :fail )
popd

rem ---- 4. free the port ----------------------------------------------------
set "FOUND="
for /f "tokens=5" %%p in ('netstat -ano -p tcp ^| findstr /r /c:":%IMPRESS_PORT% .*LISTENING"') do (
  if not "%%p"=="0" (
    if not defined FOUND echo ==^> Port %IMPRESS_PORT% is in use: stopping it
    set "FOUND=1"
    for /f "tokens=1 delims=," %%n in ('tasklist /fi "PID eq %%p" /fo csv /nh') do echo     %%p  %%~n
    taskkill /PID %%p /T /F >nul 2>&1 || echo     could not stop %%p ^(run as administrator?^)
  )
)
if defined FOUND (
  timeout /t 1 /nobreak >nul
  netstat -ano -p tcp | findstr /r /c:":%IMPRESS_PORT% .*LISTENING" >nul && (
    echo Error: port %IMPRESS_PORT% is still in use; choose another with set IMPRESS_PORT=...
    goto :fail
  )
)

rem ---- 5. start ------------------------------------------------------------
if "%IMPRESS_HOST%"=="127.0.0.1" (
  echo Listening on 127.0.0.1: only this computer can connect. For classroom gateways run
  echo   set IMPRESS_HOST=0.0.0.0 ^& launcher.bat   and allow TCP %IMPRESS_PORT% in Windows Defender Firewall.
)
echo ==^> Starting imPress on http://%IMPRESS_HOST%:%IMPRESS_PORT%  (Ctrl+C stops it)
cd /d "%BACKEND%"
rem One worker: the presence sweep, the schedulers and the WebSocket rooms live in the process.
set "TLS="
if defined IMPRESS_SSL_CERTFILE set "TLS=--ssl-certfile "%IMPRESS_SSL_CERTFILE%" --ssl-keyfile "%IMPRESS_SSL_KEYFILE%""
if not defined IMPRESS_FORWARDED_ALLOW_IPS set "IMPRESS_FORWARDED_ALLOW_IPS=127.0.0.1"
"%VPY%" -m uvicorn app.main:app --host %IMPRESS_HOST% --port %IMPRESS_PORT% --workers 1 --proxy-headers --forwarded-allow-ips %IMPRESS_FORWARDED_ALLOW_IPS% %TLS%
exit /b %errorlevel%

:find_python
set "PY="
for %%c in ("py -3.14" "py -3.13" "py -3.12" "python" "python3") do (
  if not defined PY (
    %%~c -c "%CHECK%" >nul 2>&1 && set "PY=%%~c"
  )
)
exit /b 0

:fail
echo.
pause
exit /b 1
