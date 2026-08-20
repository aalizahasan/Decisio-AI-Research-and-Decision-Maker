import sys
import os
import traceback
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Resolve absolute backend path
current_file = Path(__file__).resolve()
root_dir = current_file.parent.parent
backend_dir = root_dir / "backend"

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

app = None
init_error = None

try:
    from app.main import app as main_app
    app = main_app
except Exception as err:
    init_error = f"IMPORT_ERROR: {str(err)}\n{traceback.format_exc()}"

if not app:
    app = FastAPI(title="Diagnostic Fallback")

    @app.get("/{full_path:path}")
    def catch_all(full_path: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "Vercel Python Serverless Import Error",
                "detail": init_error,
                "sys_path": sys.path,
                "current_file": str(current_file),
                "backend_dir_exists": backend_dir.exists(),
            }
        )
