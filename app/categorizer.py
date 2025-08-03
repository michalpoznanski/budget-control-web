import re
from typing import List, Dict, Any, Optional

class TransactionCategorizer:
    """
    Klasa odpowiedzialna za automatyczne przypisywanie kategorii do transakcji
    z obsługą uczenia się na podstawie ręcznych przypisań
    """
    
    def __init__(self, manual_categories: Optional[List[Dict[str, Any]]] = None):
        # Słownik z wzorcami dla różnych kategorii
        self.category_patterns = {
            'jedzenie': [
                r'biedronka', r'carrefour', r'lidl', r'auchan', r'tesco',
                r'żabka', r'kiosk', r'pizza', r'restauracja', r'kebab',
                r'mcdonalds', r'kfc', r'subway', r'bar', r'cafe'
            ],
            'chemia': [
                r'rossmann', r'dm', r'hebe', r'apteka', r'cosmetic',
                r'mydełko', r'szampon', r'pasta', r'proszek'
            ],
            'paliwo': [
                r'orlen', r'bp', r'shell', r'lotos', r'circle k',
                r'stacja', r'benzyna', r'diesel', r'paliwo'
            ],
            'transport': [
                r'pkp', r'pks', r'autobus', r'tramwaj', r'metro',
                r'uber', r'bolt', r'taxi', r'parking'
            ],
            'rozrywka': [
                r'kino', r'teatr', r'muzeum', r'basen', r'siłownia',
                r'netflix', r'spotify', r'youtube', r'gry'
            ],
            'rachunki': [
                r'pge', r'tauron', r'energa', r'woda', r'gaz',
                r'internet', r'telefon', r'telewizja', r'czynsz'
            ],
            'zdrowie': [
                r'lekarz', r'szpital', r'apteka', r'leki', r'badania'
            ],
            'ubrania': [
                r'h&m', r'zara', r'reserved', r'cropp', r'house',
                r'buty', r'ubrania', r'odzież'
            ]
        }
        
        # Ręczne kategorie z bazy danych
        self.manual_categories = manual_categories or []
    
    def categorize_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Przypisuje kategorie do listy transakcji
        
        Args:
            transactions: Lista transakcji do kategoryzacji
            
        Returns:
            Lista transakcji z przypisanymi kategoriami
        """
        categorized_transactions = []
        unassigned_transactions = []
        
        for transaction in transactions:
            category = self._categorize_single_transaction(transaction)
            
            if category == 'nieprzypisane':
                # Dodaj do listy nieprzypisanych transakcji
                unassigned_transactions.append(transaction)
                # Tymczasowo przypisz 'nieprzypisane'
                transaction['category'] = 'nieprzypisane'
                transaction['is_manual'] = False
            else:
                transaction['category'] = category
                transaction['is_manual'] = False
            
            categorized_transactions.append(transaction)
        
        return categorized_transactions, unassigned_transactions
    
    def _categorize_single_transaction(self, transaction: Dict[str, Any]) -> str:
        """
        Przypisuje kategorię do pojedynczej transakcji
        
        Args:
            transaction: Transakcja do kategoryzacji
            
        Returns:
            Nazwa kategorii lub 'nieprzypisane' jeśli nie znaleziono dopasowania
        """
        description = transaction['description'].lower()
        
        # Najpierw sprawdź ręczne kategorie (mają priorytet)
        for manual_rule in self.manual_categories:
            if re.search(manual_rule['fraza'], description, re.IGNORECASE):
                return manual_rule['kategoria']
        
        # Następnie sprawdź standardowe wzorce
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    return category
        
        # Jeśli nie znaleziono dopasowania, zwróć 'nieprzypisane'
        return 'nieprzypisane'
    
    def add_custom_pattern(self, category: str, pattern: str):
        """
        Dodaje własny wzorzec dla kategorii
        
        Args:
            category: Nazwa kategorii
            pattern: Wzorzec regex do dopasowania
        """
        if category not in self.category_patterns:
            self.category_patterns[category] = []
        
        self.category_patterns[category].append(pattern)
    
    def update_manual_categories(self, manual_categories: List[Dict[str, Any]]):
        """
        Aktualizuje listę ręcznych kategorii
        
        Args:
            manual_categories: Lista słowników z ręcznymi kategoriami
        """
        self.manual_categories = manual_categories
    
    def get_unassigned_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Zwraca listę transakcji, które nie zostały przypisane do żadnej kategorii
        
        Args:
            transactions: Lista transakcji
            
        Returns:
            Lista nieprzypisanych transakcji
        """
        unassigned = []
        for transaction in transactions:
            if transaction['category'] == 'nieprzypisane':
                unassigned.append(transaction)
        return unassigned 