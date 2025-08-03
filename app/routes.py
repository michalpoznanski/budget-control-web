from fastapi import FastAPI, APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional

from .parser import CSVParser
from .categorizer import TransactionCategorizer
from .analyzer import ExpenseAnalyzer
from .storage import (
    save_analysis, get_analysis_history, wczytaj_reczne_kategorie,
    get_nieprzypisane_transakcje, przypisz_kategorie_transakcji,
    usun_regule_kategorii, init_db
)

# Główna aplikacja FastAPI
app = FastAPI(title="Budget Control Web", description="Aplikacja do analizy wydatków")

# Montowanie plików statycznych
app.mount("/static", StaticFiles(directory="static"), name="static")

# Konfiguracja szablonów Jinja2
templates = Jinja2Templates(directory="templates")

# Inicjalizacja bazy danych
@app.on_event("startup")
async def startup_event():
    init_db()

router = APIRouter()

# Healthcheck endpoint dla Railway
@router.get("/health")
async def health_check():
    return {"message": "Budget Control Web API", "status": "healthy"}

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Główna strona z formularzem uploadu CSV i historią analiz
    """
    # Pobierz historię analiz z bazy danych
    history = get_analysis_history()
    
    # Pobierz liczbę nieprzypisanych transakcji
    nieprzypisane = get_nieprzypisane_transakcje()
    nieprzypisane_count = len(nieprzypisane)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "history": history,
        "nieprzypisane_count": nieprzypisane_count
    })

@router.post("/analyze")
async def analyze_csv(
    request: Request,
    csv_file: UploadFile = File(...),
    week_start_date: Optional[str] = Form(None)
):
    """
    Analizuje przesłany plik CSV z transakcjami
    """
    try:
        # Wczytaj ręczne kategorie z bazy danych
        manual_categories = wczytaj_reczne_kategorie()
        
        # Wczytaj i sparsuj plik CSV
        parser = CSVParser()
        transactions = parser.parse_csv(csv_file)
        
        # Przypisz kategorie do transakcji (z obsługą uczenia się)
        categorizer = TransactionCategorizer(manual_categories)
        categorized_transactions, unassigned_transactions = categorizer.categorize_transactions(transactions)
        
        # Przeanalizuj wydatki
        analyzer = ExpenseAnalyzer()
        analysis_result = analyzer.analyze_expenses(categorized_transactions, week_start_date)
        
        # Zapisz wynik do bazy danych
        save_analysis(analysis_result)
        
        # Jeśli są nieprzypisane transakcje, przekieruj do strony ręcznego przypisywania
        if unassigned_transactions:
            return RedirectResponse(url="/manual?new_analysis=true", status_code=303)
        
        # Przekieruj z powrotem na stronę główną z komunikatem o sukcesie
        return RedirectResponse(url="/?success=true", status_code=303)
        
    except Exception as e:
        # Przekieruj z komunikatem o błędzie
        return RedirectResponse(url=f"/?error={str(e)}", status_code=303)

@router.get("/manual", response_class=HTMLResponse)
async def manual_categorization(request: Request):
    """
    Strona do ręcznego przypisywania kategorii do nieprzypisanych transakcji
    """
    # Pobierz nieprzypisane transakcje
    nieprzypisane = get_nieprzypisane_transakcje()
    
    # Pobierz dostępne kategorie
    kategorie = [
        'jedzenie', 'chemia', 'paliwo', 'transport', 'rozrywka',
        'rachunki', 'zdrowie', 'ubrania', 'inne'
    ]
    
    # Sprawdź czy to nowa analiza
    new_analysis = request.query_params.get('new_analysis') == 'true'
    
    return templates.TemplateResponse("manual.html", {
        "request": request,
        "nieprzypisane": nieprzypisane,
        "kategorie": kategorie,
        "new_analysis": new_analysis
    })

@router.post("/manual/assign")
async def assign_category(
    request: Request,
    transaction_id: int = Form(...),
    kategoria: str = Form(...),
    fraza: Optional[str] = Form(None)
):
    """
    Przypisuje kategorię do transakcji
    """
    try:
        # Przypisz kategorię do transakcji
        success = przypisz_kategorie_transakcji(transaction_id, kategoria, fraza)
        
        if success:
            return RedirectResponse(url="/manual?success=true", status_code=303)
        else:
            return RedirectResponse(url="/manual?error=Przypisanie_kategorii_nie_powiodło_się", status_code=303)
            
    except Exception as e:
        return RedirectResponse(url=f"/manual?error={str(e)}", status_code=303)

@router.post("/manual/assign-all")
async def assign_category_to_all(
    request: Request,
    fraza: str = Form(...),
    kategoria: str = Form(...)
):
    """
    Przypisuje kategorię do wszystkich transakcji zawierających daną frazę
    """
    try:
        # Pobierz nieprzypisane transakcje
        nieprzypisane = get_nieprzypisane_transakcje()
        
        # Znajdź transakcje zawierające frazę
        import re
        matching_transactions = []
        for trans in nieprzypisane:
            if re.search(fraza, trans['description'], re.IGNORECASE):
                matching_transactions.append(trans['id'])
        
        # Przypisz kategorię do wszystkich pasujących transakcji
        success_count = 0
        for transaction_id in matching_transactions:
            if przypisz_kategorie_transakcji(transaction_id, kategoria, fraza):
                success_count += 1
        
        if success_count > 0:
            return RedirectResponse(url=f"/manual?success=Przypisano_kategorię_do_{success_count}_transakcji", status_code=303)
        else:
            return RedirectResponse(url="/manual?error=Brak_pasujących_transakcji", status_code=303)
            
    except Exception as e:
        return RedirectResponse(url=f"/manual?error={str(e)}", status_code=303)

@router.get("/rules", response_class=HTMLResponse)
async def view_rules(request: Request):
    """
    Strona z listą reguł ręcznej kategoryzacji
    """
    # Pobierz reguły z bazy danych
    reguly = wczytaj_reczne_kategorie()
    
    return templates.TemplateResponse("rules.html", {
        "request": request,
        "reguly": reguly
    })

@router.post("/rules/delete")
async def delete_rule(
    request: Request,
    regula_id: int = Form(...)
):
    """
    Usuwa regułę kategoryzacji
    """
    try:
        success = usun_regule_kategorii(regula_id)
        
        if success:
            return RedirectResponse(url="/rules?success=Reguła_została_usunięta", status_code=303)
        else:
            return RedirectResponse(url="/rules?error=Usuwanie_reguły_nie_powiodło_się", status_code=303)
            
    except Exception as e:
        return RedirectResponse(url=f"/rules?error={str(e)}", status_code=303) 

# Dodanie routera do aplikacji
app.include_router(router) 