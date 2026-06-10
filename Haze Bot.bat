@echo off
title 🍃 Haze Bot Launcher (Auto-Start)
:: --- AUTO-START SEQUENCE ---
echo Launching Haze Bot Singularity... 🌬️

:: Check if Python exists in the hardcoded path
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    "%LocalAppData%\Programs\Python\Python312\python.exe" bot.py
) else (
    :: Fallback to system-wide python if the specific path isn't found
    echo [!] Local Python 3.12 not found, attempting system-wide launch...
    python bot.py
)

:: If the bot crashes, don't just close the window
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Bot process terminated unexpectedly.
    echo Restarting in 5 seconds...
    timeout /t 5
    goto :run_bot
)

pause
exit

:run_bot
"%LocalAppData%\Programs\Python\Python312\python.exe" bot.py || python bot.py
goto :run_bot
