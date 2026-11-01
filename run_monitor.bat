@echo off
title Telecom Sheet Monitor to Telegram
cd /d "%~dp0"
echo Starting Telecom Sheet Monitor...
"C:\Users\EXPRESS\.local\bin\python3.11.exe" monitor.py
pause
