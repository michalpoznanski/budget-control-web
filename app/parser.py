import csv
import io
from typing import List, Dict, Any
from datetime import datetime

class CSVParser:
    """
    Klasa odpowiedzialna za parsowanie plików CSV z transakcjami bankowymi
    """
    
    def __init__(self):
        self.expected_columns = ['data', 'opis', 'kwota', 'saldo']
    
    def parse_csv(self, file: Any) -> List[Dict[str, Any]]:
        """
        Parsuje plik CSV i zwraca listę transakcji
        
        Args:
            file: Plik CSV do sparsowania
            
        Returns:
            Lista słowników z transakcjami
        """
        transactions = []
        
        # Wczytaj zawartość pliku
        content = file.file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))
        
        # Sprawdź czy plik ma wymagane kolumny
        if not self._validate_columns(csv_reader.fieldnames):
            raise ValueError("Nieprawidłowy format pliku CSV")
        
        # Parsuj każdy wiersz
        for row in csv_reader:
            transaction = self._parse_row(row)
            if transaction:
                transactions.append(transaction)
        
        return transactions
    
    def _validate_columns(self, fieldnames: List[str]) -> bool:
        """
        Sprawdza czy plik CSV ma wymagane kolumny
        """
        if not fieldnames:
            return False
        
        return all(col in fieldnames for col in self.expected_columns)
    
    def _parse_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Parsuje pojedynczy wiersz CSV do słownika transakcji
        """
        try:
            # Parsuj datę
            date = datetime.strptime(row['data'], '%Y-%m-%d')
            
            # Parsuj kwotę
            amount = float(row['kwota'].replace(',', '.'))
            
            return {
                'date': date,
                'description': row['opis'],
                'amount': amount,
                'balance': float(row['saldo'].replace(',', '.')),
                'category': None  # Będzie przypisana przez categorizer
            }
        except (ValueError, KeyError) as e:
            # Pomiń nieprawidłowe wiersze
            return None 