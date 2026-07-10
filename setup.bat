@echo off
title DocuStudio setup
echo Installing DocuStudio dependencies...
py -m pip install --upgrade pip
py -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
  echo.
  echo Something failed. Make sure Python 3.10+ is installed from python.org
  echo with the "Add to PATH" box ticked, then run setup.bat again.
) else (
  echo.
  echo Done! Run run.bat to open DocuStudio.
)
pause
