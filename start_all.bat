@echo off
echo ========================================
echo  Dynamic ETL Pipeline System Launcher
echo ========================================
echo.
echo Starting all services...
echo.

echo [1/3] Starting Ollama (if not already running)...
start "Ollama" cmd /k "ollama serve"
timeout /t 3 /nobreak >nul

echo [2/3] Starting Backend (FastAPI)...
start "Backend" cmd /k "cd backend && fastapi dev main.py"
timeout /t 5 /nobreak >nul

echo [3/3] Starting Frontend (Streamlit)...
start "Frontend" cmd /k "cd frontend_streamlit && streamlit run app.py"

echo.
echo ========================================
echo  All services started!
echo ========================================
echo.
echo  Backend API:  http://localhost:8000/docs
echo  Frontend UI:  http://localhost:8501
echo.
echo Press any key to exit this window (services will continue running)...
pause >nul
