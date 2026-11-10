@echo off
REM Idiograph, Windows. Double-click this file. Closing its window stops the server.
REM
REM The app's folder is this file's own. Its Python environment, .venv, is looked for beside it
REM first, as a downloaded copy keeps it, and then two folders up, at the root of the repo the folder
REM sits in, from where the server starts as it always has. With neither, the first run makes .venv
REM beside it with the Python it finds, py -3 first and then python, of 3.11 or later, and installs
REM openpyxl into it, so the second run starts at once. The setup is made under another name and
REM takes the name .venv only once openpyxl is in it, so a setup that fails or is stopped never
REM leaves a .venv behind. No line here has a bracket in it outside quotes, so a folder name with
REM one cannot break the script.
setlocal
set "HERE=%~dp0"
REM the versions packaging/build_mac.py pins, so the app runs on the same openpyxl either way, and on
REM the same et_xmlfile, which openpyxl writes with when there is no lxml, as GitHub's suite pins it
set "OPENPYXL=openpyxl==3.1.5"
set "ET_XMLFILE=et_xmlfile==2.0.0"
REM and cryptography, which seals Working together's messages
set "CRYPTOGRAPHY=cryptography==50.0.2"
REM Quit in Settings names this file as the way to open the app again
set "IDIOGRAPH_START=run.bat"

if exist "%HERE%.venv\Scripts\python.exe" goto beside
if exist "%HERE%..\..\.venv\Scripts\python.exe" goto repo
goto setup

:beside
cd /d "%HERE%"
"%HERE%.venv\Scripts\python.exe" server.py %*
goto done

:repo
cd /d "%HERE%..\.."
".venv\Scripts\python.exe" "%HERE%server.py" %*
goto done

:setup
REM The first run. py -3, the launcher python.org's installer adds, then python.
set "PY="
set "SEEN="
py -3 -c "import sys" >nul 2>&1 && set "SEEN=1"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1 && set "PY=py -3"
if defined PY goto make
python -c "import sys" >nul 2>&1 && set "SEEN=1"
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1 && set "PY=python"
if defined PY goto make
if defined SEEN echo Idiograph needs Python 3.11 or later, and the one on this computer is older.
if not defined SEEN echo Idiograph needs Python 3.11 or later, and there is none on this computer.
echo Install it from https://www.python.org/downloads/ and open run.bat again.
echo In its installer, tick "Add python.exe to PATH" before Install Now.
pause
exit /b 1

:make
echo Setting up Idiograph, once. It takes a minute.
if exist "%HERE%.venv-setup" rmdir /s /q "%HERE%.venv-setup"
%PY% -m venv "%HERE%.venv-setup" || goto failed
"%HERE%.venv-setup\Scripts\python.exe" -m pip install --disable-pip-version-check -q "%OPENPYXL%" "%ET_XMLFILE%" "%CRYPTOGRAPHY%" || goto failed
if exist "%HERE%.venv" rmdir /s /q "%HERE%.venv"
ren "%HERE%.venv-setup" .venv || goto failed
goto beside

:failed
if exist "%HERE%.venv-setup" rmdir /s /q "%HERE%.venv-setup"
echo Idiograph could not set itself up, so nothing was kept. Check the internet connection and open run.bat again.
pause
exit /b 1

:done
REM a server that stopped on an error keeps its window open, so its last lines can be read
if errorlevel 1 pause
