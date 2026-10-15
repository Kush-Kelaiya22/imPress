@echo off
rem imPress launcher for Windows: everything from a fresh checkout to a running
rem server, without Docker. Safe to run every time (double-click or from cmd).
rem
rem   launcher.bat                          listens on all interfaces at port 8000
rem   launcher.bat --test-mode              test mode forced on (a lab); --no-test-mode; --no-ota; --feature name=value
rem
rem 1. finds Python 3.12+ (installs it with winget when missing)
rem 2. creates backend\.venv and installs the dependencies (pip skips what is there)
rem 3. creates backend\.env with fresh secrets if it does not exist (keeps existing values)
rem 4. checks port 8000 and asks before stopping its current owner
rem 5. starts the server
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "ROOT=%CD%"
set "BACKEND=%ROOT%\backend"
set "IMPRESS_HOST=0.0.0.0"
set "IMPRESS_PORT=8000"
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
set "PIDS="
for /f "tokens=5" %%p in ('netstat -ano -p tcp ^| findstr /r /c:":%IMPRESS_PORT% .*LISTENING"') do (
  if not "%%p"=="0" (
    set "PIDS=!PIDS! %%p"
  )
)
if defined PIDS (
  echo ==^> Port %IMPRESS_PORT% is already in use by:
  for %%p in (!PIDS!) do (
    for /f "tokens=1 delims=," %%n in ('tasklist /fi "PID eq %%p" /fo csv /nh') do echo     PID %%p  %%~n
  )
  set "CONFIRM="
  set /p "CONFIRM=Stop these process(es) so imPress can use port %IMPRESS_PORT%? [y/N] "
  if /I not "!CONFIRM!"=="y" goto :declined
  for %%p in (!PIDS!) do taskkill /PID %%p /T >nul 2>&1
  timeout /t 5 /nobreak >nul
  set "REMAINING="
  for /f "tokens=5" %%p in ('netstat -ano -p tcp ^| findstr /r /c:":%IMPRESS_PORT% .*LISTENING"') do (
    if not "%%p"=="0" set "REMAINING=!REMAINING! %%p"
  )
  if defined REMAINING (
    echo The listener did not exit after a graceful stop:
    for %%p in (!REMAINING!) do (
      for /f "tokens=1 delims=," %%n in ('tasklist /fi "PID eq %%p" /fo csv /nh') do echo     PID %%p  %%~n
    )
    set "CONFIRM="
    set /p "CONFIRM=Force-kill these remaining process(es)? [y/N] "
    if /I not "!CONFIRM!"=="y" goto :declined
    for %%p in (!REMAINING!) do taskkill /PID %%p /T /F >nul 2>&1
    timeout /t 1 /nobreak >nul
    netstat -ano -p tcp | findstr /r /c:":%IMPRESS_PORT% .*LISTENING" >nul && goto :still_busy
  )
)

rem ---- 5. start ------------------------------------------------------------
echo Listening on all network interfaces (%IMPRESS_HOST%:%IMPRESS_PORT%); allow TCP %IMPRESS_PORT% in Windows Defender Firewall.
echo ==^> Starting imPress on all network interfaces (%IMPRESS_HOST%:%IMPRESS_PORT%)  (Ctrl+C stops it)
cd /d "%BACKEND%"
rem One worker: the presence sweep, the schedulers and the WebSocket rooms live in the process.
rem Launch flags after the command (launcher.bat --test-mode ^| --no-test-mode ^| --no-ota ^| --feature name=value)
rem go to app.serve; TLS comes from IMPRESS_SSL_CERTFILE / IMPRESS_SSL_KEYFILE.
if not defined IMPRESS_FORWARDED_ALLOW_IPS set "IMPRESS_FORWARDED_ALLOW_IPS=127.0.0.1"
"%VPY%" -m app.serve --host %IMPRESS_HOST% --port %IMPRESS_PORT% %*
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

:declined
echo No process was stopped. Rerun and confirm if you want to replace it.
goto :fail

:still_busy
echo Error: port %IMPRESS_PORT% is still in use; stop its owner manually and retry.
goto :fail
