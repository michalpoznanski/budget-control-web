import unittest
from datetime import datetime, timedelta
from app.analyzer import ExpenseAnalyzer

class TestExpenseAnalyzer(unittest.TestCase):
    """
    Testy dla klasy ExpenseAnalyzer
    """
    
    def setUp(self):
        """
        Przygotowanie danych testowych
        """
        self.analyzer = ExpenseAnalyzer()
        
        # Przykładowe transakcje testowe
        self.test_transactions = [
            {
                'date': datetime.now(),
                'description': 'Biedronka - zakupy',
                'amount': -50.0,
                'balance': 1000.0,
                'category': 'jedzenie'
            },
            {
                'date': datetime.now() - timedelta(days=1),
                'description': 'Orlen - paliwo',
                'amount': -100.0,
                'balance': 1050.0,
                'category': 'paliwo'
            },
            {
                'date': datetime.now() - timedelta(days=2),
                'description': 'Rossmann - chemia',
                'amount': -30.0,
                'balance': 1150.0,
                'category': 'chemia'
            }
        ]
    
    def test_analyze_expenses(self):
        """
        Test analizy wydatków
        """
        result = self.analyzer.analyze_expenses(self.test_transactions)
        
        # Sprawdź czy wynik zawiera wymagane pola
        self.assertIn('total_expenses', result)
        self.assertIn('avg_daily_expense', result)
        self.assertIn('category_totals', result)
        self.assertIn('transaction_count', result)
        
        # Sprawdź czy suma wydatków jest poprawna
        expected_total = 50.0 + 100.0 + 30.0  # Suma wartości bezwzględnych
        self.assertEqual(result['total_expenses'], expected_total)
        
        # Sprawdź czy liczba transakcji jest poprawna
        self.assertEqual(result['transaction_count'], 3)
    
    def test_calculate_category_totals(self):
        """
        Test obliczania sum według kategorii
        """
        category_totals = self.analyzer._calculate_category_totals(self.test_transactions)
        
        # Sprawdź czy kategorie są poprawnie zsumowane
        self.assertEqual(category_totals['jedzenie'], 50.0)
        self.assertEqual(category_totals['paliwo'], 100.0)
        self.assertEqual(category_totals['chemia'], 30.0)
    
    def test_calculate_percentage_change(self):
        """
        Test obliczania procentowej zmiany
        """
        # Test wzrostu
        change = self.analyzer._calculate_percentage_change(120, 100)
        self.assertEqual(change, 20.0)
        
        # Test spadku
        change = self.analyzer._calculate_percentage_change(80, 100)
        self.assertEqual(change, -20.0)
        
        # Test z zerem
        change = self.analyzer._calculate_percentage_change(50, 0)
        self.assertEqual(change, 100.0)

if __name__ == '__main__':
    unittest.main() 