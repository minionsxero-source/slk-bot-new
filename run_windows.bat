@echo off
setlocal
python --version
if errorlevel 1 (
  echo Python was not found. Install Python 3.14 and enable "Add Python to PATH".
  pause
  exit /b 1
)
echo.
echo Running SLK Twelve Data candle test...
python run_once.py
if errorlevel 1 (
  echo.
  echo The test failed. Copy the error shown above and send it to ChatGPT.
)
pause
