from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Konfiguracja szablonów Jinja2
templates = Jinja2Templates(directory="templates")

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
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

@router.post("/analyze")
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
        
        # Wczytaj plik CSV jako pandas DataFrame
        import pandas as pd
        import io
        
        content = await csv_file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # Wyciągnij kolumny: data, opis, kwota
        transactions = []
        for _, row in df.iterrows():
            transaction = {
                'data': str(row.get('data', row.get('Data', row.get('DATA', ''))),
                'opis': str(row.get('opis', row.get('Opis', row.get('OPIS', ''))),
                'kwota': float(row.get('kwota', row.get('Kwota', row.get('KWOTA', 0)))
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