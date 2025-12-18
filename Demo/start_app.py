import subprocess
import time
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")
ACTIVATE_PS1 = os.path.join(ROOT, ".venv", "Scripts", "Activate.ps1")

def run_backend():
    ps_cmd = f'& "{ACTIVATE_PS1}"; cd "{BACKEND_DIR}"; uv run uvicorn app:app --reload --port 8000'
    subprocess.Popen(
        ["powershell", "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

def run_frontend():
    time.sleep(2)
    ps_cmd = f'& "{ACTIVATE_PS1}"; cd "{FRONTEND_DIR}"; uv run streamlit run streamlit_app.py'
    subprocess.Popen(
        ["powershell", "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

if __name__ == "__main__":
    run_backend()
    run_frontend()