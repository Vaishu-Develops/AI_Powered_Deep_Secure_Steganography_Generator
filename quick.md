.\venv\Scripts\Activate.ps1  
cd d:\Stegen\backend
python main.py
uvicorn main:app --reload --host 0.0.0.0 --port 8000

cd d:\Stegen\frontend
pnpm run dev