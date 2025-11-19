@echo off
echo Starting Newsly Frontend...
python -m uvicorn frontend.server:app --host 0.0.0.0 --port 8000 --reload
pause
