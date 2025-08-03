from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import Base, AnalizaTygodnia, Transakcja, ReczneKategorie

class DatabaseManager:
    """
    Klasa do zarządzania bazą danych SQLite
    """
    
    def __init__(self, database_url: str = "sqlite:///database.db"):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def init_db(self):
        """
        Inicjalizuje bazę danych - tworzy tabele
        """
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """
        Zwraca sesję bazy danych
        """
        return self.SessionLocal()

# Globalna instancja menedżera bazy danych
db_manager = DatabaseManager()

def init_db():
    """
    Inicjalizuje bazę danych
    """
    db_manager.init_db()

def save_analysis(analysis_result: Dict[str, Any]) -> int:
    """
    Zapisuje wynik analizy do bazy danych
    
    Args:
        analysis_result: Wynik analizy z analyzer.py
        
    Returns:
        ID zapisanej analizy
    """
    session = db_manager.get_session()
    
    try:
        # Utwórz nową analizę tygodniową
        analiza = AnalizaTygodnia(
            week_start=analysis_result['week_start'],
            week_end=analysis_result['week_end'],
            total_expenses=analysis_result['total_expenses'],
            avg_daily_expense=analysis_result['avg_daily_expense'],
            transaction_count=analysis_result['transaction_count'],
            analysis_date=datetime.fromisoformat(analysis_result['analysis_date'])
        )
        
        session.add(analiza)
        session.flush()  # Aby uzyskać ID analizy
        
        # Zapisz transakcje
        for transaction_data in analysis_result['transactions']:
            transakcja = Transakcja(
                analiza_id=analiza.id,
                date=transaction_data['date'],
                description=transaction_data['description'],
                amount=transaction_data['amount'],
                balance=transaction_data['balance'],
                category=transaction_data['category'],
                is_manual=transaction_data.get('is_manual', False)
            )
            session.add(transakcja)
        
        session.commit()
        return analiza.id
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_analysis_history(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Pobiera historię analiz z bazy danych
    
    Args:
        limit: Maksymalna liczba analiz do pobrania
        
    Returns:
        Lista analiz z podstawowymi informacjami
    """
    session = db_manager.get_session()
    
    try:
        # Pobierz ostatnie analizy
        analizy = session.query(AnalizaTygodnia).order_by(
            AnalizaTygodnia.analysis_date.desc()
        ).limit(limit).all()
        
        history = []
        for analiza in analizy:
            history.append({
                'id': analiza.id,
                'week_start': analiza.week_start,
                'week_end': analiza.week_end,
                'total_expenses': analiza.total_expenses,
                'avg_daily_expense': analiza.avg_daily_expense,
                'transaction_count': analiza.transaction_count,
                'analysis_date': analiza.analysis_date.isoformat()
            })
        
        return history
        
    finally:
        session.close()

def get_analysis_by_id(analysis_id: int) -> Optional[Dict[str, Any]]:
    """
    Pobiera szczegółową analizę po ID
    
    Args:
        analysis_id: ID analizy
        
    Returns:
        Szczegółowa analiza z transakcjami lub None
    """
    session = db_manager.get_session()
    
    try:
        analiza = session.query(AnalizaTygodnia).filter(
            AnalizaTygodnia.id == analysis_id
        ).first()
        
        if not analiza:
            return None
        
        # Pobierz transakcje dla tej analizy
        transakcje = session.query(Transakcja).filter(
            Transakcja.analiza_id == analysis_id
        ).all()
        
        return {
            'id': analiza.id,
            'week_start': analiza.week_start,
            'week_end': analiza.week_end,
            'total_expenses': analiza.total_expenses,
            'avg_daily_expense': analiza.avg_daily_expense,
            'transaction_count': analiza.transaction_count,
            'analysis_date': analiza.analysis_date.isoformat(),
            'transactions': [
                {
                    'date': t.date,
                    'description': t.description,
                    'amount': t.amount,
                    'balance': t.balance,
                    'category': t.category,
                    'is_manual': t.is_manual
                }
                for t in transakcje
            ]
        }
        
    finally:
        session.close()

def get_previous_week_analysis(current_week_start: str) -> Optional[Dict[str, Any]]:
    """
    Pobiera analizę poprzedniego tygodnia dla porównania
    
    Args:
        current_week_start: Data rozpoczęcia bieżącego tygodnia
        
    Returns:
        Analiza poprzedniego tygodnia lub None
    """
    from datetime import datetime, timedelta
    
    current_date = datetime.strptime(current_week_start, '%Y-%m-%d')
    previous_week_start = (current_date - timedelta(days=7)).strftime('%Y-%m-%d')
    
    session = db_manager.get_session()
    
    try:
        analiza = session.query(AnalizaTygodnia).filter(
            AnalizaTygodnia.week_start == previous_week_start
        ).first()
        
        if not analiza:
            return None
        
        return get_analysis_by_id(analiza.id)
        
    finally:
        session.close()

# Nowe funkcje dla ręcznych kategorii

def zapisz_reczne_kategorie(fraza: str, kategoria: str) -> bool:
    """
    Zapisuje nową regułę ręcznej kategoryzacji
    
    Args:
        fraza: Fraza do dopasowania w opisie transakcji
        kategoria: Kategoria do przypisania
        
    Returns:
        True jeśli zapisano pomyślnie, False w przeciwnym razie
    """
    session = db_manager.get_session()
    
    try:
        # Sprawdź czy reguła już istnieje
        existing = session.query(ReczneKategorie).filter(
            ReczneKategorie.fraza == fraza
        ).first()
        
        if existing:
            # Aktualizuj istniejącą regułę
            existing.kategoria = kategoria
            existing.liczba_uzyc += 1
            existing.data_ostatniego_uzycia = datetime.now()
        else:
            # Utwórz nową regułę
            nowa_regula = ReczneKategorie(
                fraza=fraza,
                kategoria=kategoria,
                liczba_uzyc=1,
                data_utworzenia=datetime.now(),
                data_ostatniego_uzycia=datetime.now()
            )
            session.add(nowa_regula)
        
        session.commit()
        return True
        
    except Exception as e:
        session.rollback()
        return False
    finally:
        session.close()

def wczytaj_reczne_kategorie() -> List[Dict[str, Any]]:
    """
    Wczytuje wszystkie reguły ręcznej kategoryzacji
    
    Returns:
        Lista słowników z regułami kategoryzacji
    """
    session = db_manager.get_session()
    
    try:
        reguly = session.query(ReczneKategorie).order_by(
            ReczneKategorie.liczba_uzyc.desc()
        ).all()
        
        return [
            {
                'id': regula.id,
                'fraza': regula.fraza,
                'kategoria': regula.kategoria,
                'liczba_uzyc': regula.liczba_uzyc,
                'data_utworzenia': regula.data_utworzenia.isoformat(),
                'data_ostatniego_uzycia': regula.data_ostatniego_uzycia.isoformat()
            }
            for regula in reguly
        ]
        
    finally:
        session.close()

def get_nieprzypisane_transakcje() -> List[Dict[str, Any]]:
    """
    Pobiera wszystkie transakcje z kategorią 'nieprzypisane'
    
    Returns:
        Lista nieprzypisanych transakcji
    """
    session = db_manager.get_session()
    
    try:
        transakcje = session.query(Transakcja).filter(
            Transakcja.category == 'nieprzypisane'
        ).order_by(Transakcja.date.desc()).all()
        
        return [
            {
                'id': t.id,
                'analiza_id': t.analiza_id,
                'date': t.date,
                'description': t.description,
                'amount': t.amount,
                'balance': t.balance,
                'category': t.category,
                'is_manual': t.is_manual
            }
            for t in transakcje
        ]
        
    finally:
        session.close()

def przypisz_kategorie_transakcji(transaction_id: int, kategoria: str, fraza: str = None) -> bool:
    """
    Przypisuje kategorię do transakcji i opcjonalnie zapisuje regułę
    
    Args:
        transaction_id: ID transakcji
        kategoria: Kategoria do przypisania
        fraza: Fraza do zapisania jako reguła (opcjonalna)
        
    Returns:
        True jeśli przypisano pomyślnie, False w przeciwnym razie
    """
    session = db_manager.get_session()
    
    try:
        # Znajdź transakcję
        transakcja = session.query(Transakcja).filter(
            Transakcja.id == transaction_id
        ).first()
        
        if not transakcja:
            return False
        
        # Zaktualizuj kategorię
        transakcja.category = kategoria
        transakcja.is_manual = True
        
        # Jeśli podano frazę, zapisz regułę
        if fraza:
            zapisz_reczne_kategorie(fraza, kategoria)
        
        session.commit()
        return True
        
    except Exception as e:
        session.rollback()
        return False
    finally:
        session.close()

def usun_regule_kategorii(regula_id: int) -> bool:
    """
    Usuwa regułę ręcznej kategoryzacji
    
    Args:
        regula_id: ID reguły do usunięcia
        
    Returns:
        True jeśli usunięto pomyślnie, False w przeciwnym razie
    """
    session = db_manager.get_session()
    
    try:
        regula = session.query(ReczneKategorie).filter(
            ReczneKategorie.id == regula_id
        ).first()
        
        if regula:
            session.delete(regula)
            session.commit()
            return True
        
        return False
        
    except Exception as e:
        session.rollback()
        return False
    finally:
        session.close() 