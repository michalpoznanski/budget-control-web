FROM python:3.11-slim

# Ustawienie katalogu roboczego
WORKDIR /app

# Kopiowanie plików zależności
COPY requirements.txt .

# Instalacja zależności
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie kodu aplikacji
COPY . .

# Utworzenie katalogu dla bazy danych
RUN mkdir -p /app/data

# Ustawienie zmiennych środowiskowych
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///data/database.db

# Ekspozycja portu
EXPOSE 8000

# Komenda uruchamiająca aplikację
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 