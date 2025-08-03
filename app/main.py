import os
import uvicorn
import csv
import io
from datetime import datetime
from dateutil import parser as date_parser
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Budget Control Web", description="Aplikacja do analizy wydatków")

# Montowanie plików statycznych
app.mount("/static", StaticFiles(directory="static"), name="static")

# Konfiguracja szablonów Jinja2
templates = Jinja2Templates(directory="templates")

# Mapa kolumn do rozpoznawania różnych formatów CSV
COLUMN_MAPPING = {
    "data": ["Data", "Data operacji", "Transaction date", "Date", "data", "DATA"],
    "kwota": ["Kwota", "Amount", "Wartość", "kwota", "KWOTA"],
    "opis": ["Opis", "Tytuł", "Title", "Description", "opis", "OPIS"],
    "saldo": ["Saldo", "Balance", "saldo", "SALDO"]
}

def detect_column_mapping(headers):
    """
    Wykrywa mapowanie kolumn na podstawie nagłówków CSV
    """
    mapping = {}
    detected_columns = []
    
    for standard_name, possible_names in COLUMN_MAPPING.items():
        for header in headers:
            if header.strip() in possible_names:
                mapping[standard_name] = header.strip()
                detected_columns.append(header.strip())
                break
    
    return mapping, detected_columns

def clean_amount(amount_str):
    """
    Czyści i konwertuje kwotę na float
    """
    if not amount_str:
        return 0.0
    
    # Usuń cudzysłowy i apostrofy
    cleaned = amount_str.replace('"', '').replace("'", '').strip()
    
    # Usuń spacje z liczb
    cleaned = cleaned.replace(' ', '')
    
    # Zamień przecinki na kropki w liczbach
    if ',' in cleaned and '.' not in cleaned:
        # Jeśli jest tylko przecinek, to prawdopodobnie separator dziesiętny
        cleaned = cleaned.replace(',', '.')
    elif ',' in cleaned and '.' in cleaned:
        # Jeśli są oba, to przecinek to separator tysięcy
        cleaned = cleaned.replace(',', '')
    
    try:
        return float(cleaned)
    except ValueError:
        print(f"Invalid amount: {amount_str}")
        return None

def parse_date(date_str):
    """
    Parsuje datę w różnych formatach
    """
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Próbuj różne formaty dat
    date_formats = [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d"
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # Jeśli nie udało się z datetime, spróbuj dateutil
    try:
        parsed_date = date_parser.parse(date_str)
        return parsed_date.strftime("%Y-%m-%d")
    except:
        print(f"Invalid date format: {date_str}")
        return None

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
        
        # Użyj csv.Sniffer do wykrycia formatu
        try:
            dialect = csv.Sniffer().sniff(csv_text[:1024])
        except:
            dialect = csv.excel  # Fallback do standardowego formatu
        
        # Parsuj CSV z wykrytym formatem
        csv_reader = csv.DictReader(io.StringIO(csv_text), dialect=dialect)
        
        # Wykryj mapowanie kolumn
        headers = csv_reader.fieldnames
        if not headers:
            return RedirectResponse(url="/?error=Nie można odczytać nagłówków CSV", status_code=303)
        
        column_mapping, detected_columns = detect_column_mapping(headers)
        
        # Sprawdź czy znaleziono wymagane kolumny
        required_columns = ["data", "kwota", "opis"]
        missing_columns = [col for col in required_columns if col not in column_mapping]
        
        if missing_columns:
            error_msg = f"Brak wymaganych kolumn: {', '.join(missing_columns)}. Wykryte kolumny: {', '.join(detected_columns)}"
            return RedirectResponse(url=f"/?error={error_msg}", status_code=303)
        
        # Przetwórz transakcje
        transactions = []
        for row in csv_reader:
            # Pobierz wartości z odpowiednich kolumn
            date_raw = row.get(column_mapping["data"], "")
            amount_raw = row.get(column_mapping["kwota"], "")
            description_raw = row.get(column_mapping["opis"], "")
            
            # Parsuj datę
            parsed_date = parse_date(date_raw)
            if not parsed_date:
                print(f"Invalid date: {date_raw}")
                continue
            
            # Parsuj kwotę
            parsed_amount = clean_amount(amount_raw)
            if parsed_amount is None:
                continue
            
            transaction = {
                'data': parsed_date,
                'opis': description_raw.strip(),
                'kwota': parsed_amount
            }
            transactions.append(transaction)
        
        if not transactions:
            return RedirectResponse(url="/?error=Nie znaleziono prawidłowych transakcji w pliku", status_code=303)
        
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