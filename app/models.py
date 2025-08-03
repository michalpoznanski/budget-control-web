from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class AnalizaTygodnia(Base):
    """
    Model dla analizy tygodniowej wydatków
    """
    __tablename__ = 'analiza_tygodnia'
    
    id = Column(Integer, primary_key=True)
    week_start = Column(String(10), nullable=False)  # YYYY-MM-DD
    week_end = Column(String(10), nullable=False)    # YYYY-MM-DD
    total_expenses = Column(Float, nullable=False)
    avg_daily_expense = Column(Float, nullable=False)
    transaction_count = Column(Integer, nullable=False)
    analysis_date = Column(DateTime, default=datetime.now)
    
    # Relacja z transakcjami
    transakcje = relationship("Transakcja", back_populates="analiza")
    
    def __repr__(self):
        return f"<AnalizaTygodnia(week_start='{self.week_start}', total_expenses={self.total_expenses})>"

class Transakcja(Base):
    """
    Model dla pojedynczej transakcji
    """
    __tablename__ = 'transakcje'
    
    id = Column(Integer, primary_key=True)
    analiza_id = Column(Integer, ForeignKey('analiza_tygodnia.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    balance = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    is_manual = Column(Boolean, default=False)  # Czy kategoria została przypisana ręcznie
    
    # Relacja z analizą
    analiza = relationship("AnalizaTygodnia", back_populates="transakcje")
    
    def __repr__(self):
        return f"<Transakcja(date='{self.date}', amount={self.amount}, category='{self.category}')>"

class ReczneKategorie(Base):
    """
    Model dla ręcznie przypisanych kategorii - uczenie się na podstawie historii
    """
    __tablename__ = 'reczne_kategorie'
    
    id = Column(Integer, primary_key=True)
    fraza = Column(String(200), nullable=False, unique=True)  # Fraza do dopasowania
    kategoria = Column(String(50), nullable=False)  # Kategoria do przypisania
    liczba_uzyc = Column(Integer, default=1)  # Liczba użyć tej reguły
    data_utworzenia = Column(DateTime, default=datetime.now)
    data_ostatniego_uzycia = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<ReczneKategorie(fraza='{self.fraza}', kategoria='{self.kategoria}')>"

class KategoriaWydatkow(Base):
    """
    Model dla kategorii wydatków (opcjonalny - do przyszłego rozszerzenia)
    """
    __tablename__ = 'kategorie_wydatkow'
    
    id = Column(Integer, primary_key=True)
    nazwa = Column(String(50), unique=True, nullable=False)
    opis = Column(Text)
    kolor = Column(String(7))  # Hex color code
    
    def __repr__(self):
        return f"<KategoriaWydatkow(nazwa='{self.nazwa}')>" 