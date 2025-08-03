import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes import router

app = FastAPI(title="Budget Control Web", description="Aplikacja do analizy wydatków")

# Montowanie plików statycznych
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dodanie routera
app.include_router(router)

# Prosty healthcheck endpoint
@app.get("/health")
async def health_check():
    return {"message": "Budget Control Web API", "status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False) 