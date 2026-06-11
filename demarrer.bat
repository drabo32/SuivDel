@echo off
echo ===== Suivi Evolutions =====

REM --- Configuration base de donnees ---
set DB_URL=postgresql://suivi:suivi2026@localhost:5432/suivi_evolutions

REM --- Creer la base si elle n'existe pas ---
echo Creation de la base de donnees...
psql -U postgres -c "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'suivi') THEN CREATE USER suivi WITH PASSWORD 'suivi2026'; END IF; END $$;"
psql -U postgres -c "SELECT 1 FROM pg_database WHERE datname='suivi_evolutions'" | findstr /C:"1 row" >nul || psql -U postgres -c "CREATE DATABASE suivi_evolutions OWNER suivi;"

REM --- Demarrer le backend ---
echo Demarrage du backend...
cd backend
if not exist ".venv" (
    echo Installation des dependances Python...
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
)
start "Backend - Suivi Evolutions" cmd /k ".venv\Scripts\activate && set DATABASE_URL=%DB_URL% && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
cd ..

REM --- Demarrer le frontend ---
echo Demarrage du frontend...
cd frontend
if not exist "node_modules" (
    echo Installation des dependances Node...
    npm install
)
start "Frontend - Suivi Evolutions" cmd /k "npm run dev"
cd ..

echo.
echo ===================================
echo Backend  : http://localhost:8000
echo API docs : http://localhost:8000/docs
echo Frontend : http://localhost:5173
echo ===================================
echo Fermez les fenetres de commande pour arreter l'application.
pause
