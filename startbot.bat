@echo off
:loop
echo Starting main.py...
python main.py

REM Check if main.py exited with an error (non-zero exit code)
IF %ERRORLEVEL% NEQ 0 (
    echo main.py crashed with exit code %ERRORLEVEL%.
    echo Restarting in 5 seconds...
    timeout /t 5
    goto loop
)

REM Exit normally if main.py ends with no error (exit code 0)
echo main.py exited successfully.
pause
