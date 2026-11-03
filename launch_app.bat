@echo off
title Personal Expense Tracker
cd /d "%~dp0"
echo ===================================================
echo   Starting Personal Expense Tracker...
echo ===================================================
echo Opening application in your default browser...
start "" "http://localhost:8501"
".\.venv\Scripts\streamlit.exe" run app.py
pause
