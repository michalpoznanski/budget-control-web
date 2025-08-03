import os
import uvicorn
import csv
import io
import pandas as pd
from datetime import datetime
from dateutil import parser as date_parser
from fastapi import FastAPI, Request, UploadFile, File, Form
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
    "data": ["data", "Data", "Data operacji", "Transaction Date", "DATA", "Date", "Transaction date"],
    "kwota": ["kwota", "Kwota", "Amount", "Wartość", "Cena", "Kwota operacji", "KWOTA"],
    "opis": ["opis", "Opis", "Tytuł", "Description", "Tytuł operacji", "OPIS", "Title"],
    "saldo": ["saldo", "Saldo", "Balance", "SALDO"]
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

def debug_csv_data(df, column_mapping=None, detected_columns=None):
    """
    Debuguje dane CSV - zapisuje do pliku i loguje informacje
    """
    try:
        # Zapisz dataframe do pliku tymczasowego
        debug_path = "/tmp/debug.csv"
        df.to_csv(debug_path, index=False)
        print(f"DEBUG: Zapisano dane CSV do {debug_path}")
        
        # Loguj informacje o kolumnach
        print(f"DEBUG: Wykryte kolumny: {list(df.columns)}")
        
        if detected_columns:
            print(f"DEBUG: Kolumny po mapowaniu: {detected_columns}")
        
        if column_mapping:
            print(f"DEBUG: Mapowanie kolumn: {column_mapping}")
        
        # Loguj pierwsze 5 wierszy
        print("DEBUG: Pierwsze 5 wierszy danych:")
        print(df.head().to_string())
        
        # Loguj informacje o dataframe
        print(f"DEBUG: Rozmiar dataframe: {df.shape}")
        print(f"DEBUG: Typy danych:")
        print(df.dtypes)
        
    except Exception as e:
        print(f"DEBUG ERROR: Nie udało się zapisać danych debug: {e}")

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
            # Przekieruj na stronę przypisywania kolumn z wykrytymi kolumnami
            columns_param = ','.join(detected_columns)
            return RedirectResponse(url=f"/assign-columns?columns={columns_param}", status_code=303)
        
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
            # Debuguj dane przed zwróceniem błędu
            try:
                df = pd.read_csv(io.StringIO(csv_text), dialect=dialect)
                debug_csv_data(df, column_mapping, detected_columns)
            except Exception as e:
                print(f"DEBUG ERROR: Nie udało się utworzyć dataframe: {e}")
            
            return RedirectResponse(url="/?error=Nie znaleziono prawidłowych transakcji w pliku", status_code=303)
        
        # Przekaż listę transakcji do szablonu
        return templates.TemplateResponse("analyze.html", {
            "request": request,
            "transactions": transactions
        })
        
    except Exception as e:
        # Przekieruj z komunikatem o błędzie
        return RedirectResponse(url=f"/?error={str(e)}", status_code=303)

@app.get("/assign-columns", response_class=HTMLResponse)
async def assign_columns_page(request: Request):
    """
    Strona do ręcznego przypisywania kolumn CSV
    """
    # Pobierz dane z sesji lub query params
    detected_columns = request.query_params.get('columns', '').split(',') if request.query_params.get('columns') else []
    
    return templates.TemplateResponse("assign_columns.html", {
        "request": request,
        "detected_columns": detected_columns
    })

@app.post("/process-csv")
async def process_csv_with_columns(
    request: Request,
    csv_file: UploadFile = File(...),
    data_column: str = Form(...),
    kwota_column: str = Form(...),
    opis_column: str = Form(...)
):
    """
    Przetwarza CSV z ręcznie przypisanymi kolumnami
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
            dialect = csv.excel
        
        # Parsuj CSV z wykrytym formatem
        csv_reader = csv.DictReader(io.StringIO(csv_text), dialect=dialect)
        
        # Sprawdź czy wybrane kolumny istnieją
        headers = csv_reader.fieldnames
        if not headers:
            return RedirectResponse(url="/?error=Nie można odczytać nagłówków CSV", status_code=303)
        
        # Sprawdź czy wybrane kolumny istnieją
        missing_columns = []
        for col in [data_column, kwota_column, opis_column]:
            if col not in headers:
                missing_columns.append(col)
        
        if missing_columns:
            error_msg = f"Wybrane kolumny nie istnieją: {', '.join(missing_columns)}. Dostępne kolumny: {', '.join(headers)}"
            return RedirectResponse(url=f"/?error={error_msg}", status_code=303)
        
        # Przetwórz transakcje z ręcznie przypisanymi kolumnami
        transactions = []
        for row in csv_reader:
            # Pobierz wartości z wybranych kolumn
            date_raw = row.get(data_column, "")
            amount_raw = row.get(kwota_column, "")
            description_raw = row.get(opis_column, "")
            
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
            # Debuguj dane przed zwróceniem błędu
            try:
                df = pd.read_csv(io.StringIO(csv_text), dialect=dialect)
                debug_csv_data(df, {"data": data_column, "kwota": kwota_column, "opis": opis_column}, [data_column, kwota_column, opis_column])
            except Exception as e:
                print(f"DEBUG ERROR: Nie udało się utworzyć dataframe: {e}")
            
            return RedirectResponse(url="/?error=Nie znaleziono prawidłowych transakcji w pliku", status_code=303)
        
        # Przekaż listę transakcji do szablonu
        return templates.TemplateResponse("analyze.html", {
            "request": request,
            "transactions": transactions
        })
        
    except Exception as e:
        return RedirectResponse(url=f"/?error={str(e)}", status_code=303)

# Prosty healthcheck endpoint
@app.get("/health")
async def health_check():
    return {"message": "Budget Control Web API", "status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False) 