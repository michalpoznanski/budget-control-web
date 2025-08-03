import os
import uvicorn
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Budget Control Web", description="Aplikacja do analizy wydatków")

# Montowanie plików statycznych
app.mount("/static", StaticFiles(directory="static"), name="static")

# Konfiguracja szablonów Jinja2
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Główna strona z formularzem uploadu CSV
    """
    # Pobierz komunikat o błędzie z query params
    error = request.query_params.get('error')
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "error": error
    })

@app.post("/analyze")
async def analyze_csv(
    request: Request,
    csv_file: UploadFile = File(...)
):
    """
    Analizuje przesłany plik CSV z transakcjami
    """
    try:
        if not csv_file:
            return RedirectResponse(url="/?error=Nie wybrano pliku", status_code=303)
        
        # Wczytaj plik CSV
        content = await csv_file.read()
        csv_text = content.decode('utf-8')
        
        # Wyciągnij kolumny: data, opis, kwota
        transactions = []
        lines = csv_text.strip().split('\n')
        
        if len(lines) < 2:
            return RedirectResponse(url="/?error=Plik CSV jest pusty lub nieprawidłowy", status_code=303)
        
        # Pobierz nagłówki
        headers = lines[0].split(',')
        
        # Przetwórz każdy wiersz
        for line in lines[1:]:
            if line.strip():
                values = line.split(',')
                if len(values) >= 3:
                    # Oczyść i przetwórz kwotę
                    kwota_raw = values[2].strip()
                    kwota_clean = kwota_raw.replace('"', '').replace("'", '')
                    
                    try:
                        kwota = float(kwota_clean) if kwota_clean else 0.0
                    except ValueError:
                        print(f"Invalid amount: {kwota_raw}")
                        continue  # Pomiń tę linię
                    
                    transaction = {
                        'data': values[0].strip(),
                        'opis': values[1].strip(),
                        'kwota': kwota
                    }
                    transactions.append(transaction)
        
        # Przekaż listę transakcji do szablonu
        return templates.TemplateResponse("analyze.html", {
            "request": request,
            "transactions": transactions
        })
        
    except Exception as e:
        # Przekieruj z komunikatem o błędzie
        return RedirectResponse(url=f"/?error={str(e)}", status_code=303)

# Prosty healthcheck endpoint
@app.get("/health")
async def health_check():
    return {"message": "Budget Control Web API", "status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False) 