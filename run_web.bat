@echo off
title BlazeAI v5 Web Server - Created by ShortCodeGuy Studio
cd /d "%~dp0"
echo ============================================================
echo           BlazeAI v5 Web Server Launcher
echo           Created by ShortCodeGuy Studio
echo ============================================================
echo Starting local AI server on http://localhost:8000 ...
echo Once started, your web browser will open automatically.
echo (Keep this terminal window open while using BlazeAI)
echo ============================================================
start "" http://localhost:8000
python server.py
pause
