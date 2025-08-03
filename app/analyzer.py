from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

class ExpenseAnalyzer:
    """
    Klasa odpowiedzialna za analizę wydatków i porównania tygodniowe
    """
    
    def __init__(self):
        self.categories = [
            'jedzenie', 'chemia', 'paliwo', 'transport', 'rozrywka',
            'rachunki', 'zdrowie', 'ubrania', 'nieprzypisane', 'inne'
        ]
    
    def analyze_expenses(self, transactions: List[Dict[str, Any]], week_start_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Analizuje wydatki z transakcji i tworzy raport tygodniowy
        
        Args:
            transactions: Lista transakcji z kategoriami
            week_start_date: Data rozpoczęcia tygodnia (opcjonalna)
            
        Returns:
            Słownik z wynikami analizy
        """
        # Określ datę rozpoczęcia tygodnia
        if week_start_date:
            week_start = datetime.strptime(week_start_date, '%Y-%m-%d')
        else:
            week_start = self._get_week_start(transactions)
        
        # Filtruj transakcje z danego tygodnia
        week_transactions = self._filter_week_transactions(transactions, week_start)
        
        # Analizuj wydatki według kategorii
        category_totals = self._calculate_category_totals(week_transactions)
        
        # Oblicz statystyki
        total_expenses = sum(category_totals.values())
        avg_daily_expense = total_expenses / 7 if week_transactions else 0
        
        # Przygotuj wynik analizy
        analysis_result = {
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': (week_start + timedelta(days=6)).strftime('%Y-%m-%d'),
            'total_expenses': total_expenses,
            'avg_daily_expense': avg_daily_expense,
            'category_totals': category_totals,
            'transaction_count': len(week_transactions),
            'transactions': week_transactions,
            'analysis_date': datetime.now().isoformat()
        }
        
        return analysis_result
    
    def compare_with_previous_week(self, current_analysis: Dict[str, Any], previous_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Porównuje analizę bieżącego tygodnia z poprzednim
        
        Args:
            current_analysis: Analiza bieżącego tygodnia
            previous_analysis: Analiza poprzedniego tygodnia
            
        Returns:
            Słownik z porównaniem
        """
        comparison = {
            'total_change': current_analysis['total_expenses'] - previous_analysis['total_expenses'],
            'total_change_percent': self._calculate_percentage_change(
                current_analysis['total_expenses'], 
                previous_analysis['total_expenses']
            ),
            'category_changes': {},
            'avg_daily_change': current_analysis['avg_daily_expense'] - previous_analysis['avg_daily_expense']
        }
        
        # Porównaj kategorie
        for category in self.categories:
            current_amount = current_analysis['category_totals'].get(category, 0)
            previous_amount = previous_analysis['category_totals'].get(category, 0)
            
            comparison['category_changes'][category] = {
                'change': current_amount - previous_amount,
                'change_percent': self._calculate_percentage_change(current_amount, previous_amount)
            }
        
        return comparison
    
    def _get_week_start(self, transactions: List[Dict[str, Any]]) -> datetime:
        """
        Określa datę rozpoczęcia tygodnia na podstawie transakcji
        """
        if not transactions:
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Znajdź najwcześniejszą datę
        earliest_date = min(transaction['date'] for transaction in transactions)
        
        # Oblicz początek tygodnia (poniedziałek)
        days_since_monday = earliest_date.weekday()
        week_start = earliest_date - timedelta(days=days_since_monday)
        
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _filter_week_transactions(self, transactions: List[Dict[str, Any]], week_start: datetime) -> List[Dict[str, Any]]:
        """
        Filtruje transakcje z danego tygodnia
        """
        week_end = week_start + timedelta(days=7)
        
        return [
            transaction for transaction in transactions
            if week_start <= transaction['date'] < week_end
        ]
    
    def _calculate_category_totals(self, transactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Oblicza sumy wydatków według kategorii
        """
        category_totals = defaultdict(float)
        
        for transaction in transactions:
            if transaction['amount'] < 0:  # Tylko wydatki (ujemne kwoty)
                category = transaction['category']
                category_totals[category] += abs(transaction['amount'])
        
        return dict(category_totals)
    
    def _calculate_percentage_change(self, current: float, previous: float) -> float:
        """
        Oblicza procentową zmianę
        """
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        
        return ((current - previous) / previous) * 100 