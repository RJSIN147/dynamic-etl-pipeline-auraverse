@echo off
echo Starting ETL Backend...
cd backend
fastapi dev main.py
pause
