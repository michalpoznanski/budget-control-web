import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

from .routes import router

# Import storage z obsługą błędów
try:
    from .storage import init_db
    STORAGE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Storage not available: {e}")
    STORAGE_AVAILABLE = False
    init_db = lambda: None

app = FastAPI(title="Budget Control Web", description="Aplikacja do analizy wydatków")

# Montowanie plików statycznych
app.mount("/static", StaticFiles(directory="static"), name="static")

# Konfiguracja szablonów Jinja2
templates = Jinja2Templates(directory="templates")

# Inicjalizacja bazy danych z obsługą błędów
@app.on_event("startup")
async def startup_event():
    if STORAGE_AVAILABLE:
        try:
            init_db()
        except Exception as e:
            print(f"Warning: Database initialization failed: {e}")
    else:
        print("Warning: Storage not available, skipping database initialization")

# Dodanie routera
app.include_router(router)

# Prosty healthcheck endpoint
@app.get("/health")
async def health_check():
    return {"message": "Budget Control Web API", "status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False) 