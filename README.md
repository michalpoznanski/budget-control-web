# 💰 Budget Control Web

Aplikacja webowa do analizy wydatków z wyciągów bankowych w formacie CSV. Projekt wykorzystuje FastAPI z Jinja2 jako frontend do automatycznego kategoryzowania transakcji i prowadzenia historii tygodniowej.

## 🚀 Funkcjonalności

- **Upload plików CSV** - wczytywanie wyciągów bankowych
- **Automatyczna kategoryzacja** - przypisywanie transakcji do kategorii (jedzenie, chemia, paliwo, etc.)
- **Analiza tygodniowa** - sumowanie wydatków według kategorii
- **Historia analiz** - przechowywanie wyników w bazie SQLite
- **Nowoczesny interfejs** - responsywny design z animacjami

## 📁 Struktura projektu

```
budget_control_web/
├── app/
│   ├── main.py          # Główna aplikacja FastAPI
│   ├── routes.py        # Routing i endpointy
│   ├── parser.py        # Parsowanie plików CSV
│   ├── categorizer.py   # Automatyczna kategoryzacja
│   ├── analyzer.py      # Analiza wydatków
│   ├── storage.py       # Zarządzanie bazą danych
│   └── models.py        # Modele SQLAlchemy
├── templates/
│   └── index.html       # Frontend z Jinja2
├── static/
│   └── style.css        # Style CSS
├── tests/
│   └── test_analyzer.py # Testy jednostkowe
├── requirements.txt     # Zależności Python
├── Dockerfile          # Konfiguracja Docker
├── railway.json        # Konfiguracja Railway
└── README.md           # Dokumentacja
```

## 🛠️ Instalacja i uruchomienie

### Lokalnie

1. **Klonowanie repozytorium**
   ```bash
   git clone <repository-url>
   cd budget_control_web
   ```

2. **Instalacja zależności**
   ```bash
   pip install -r requirements.txt
   ```

3. **Uruchomienie aplikacji**
   ```bash
   python -m app.main
   ```

4. **Otwarcie w przeglądarce**
   ```
   http://localhost:8000
   ```

### Z Docker

1. **Budowanie obrazu**
   ```bash
   docker build -t budget-control-web .
   ```

2. **Uruchomienie kontenera**
   ```bash
   docker run -p 8000:8000 budget-control-web
   ```

## 📊 Format pliku CSV

Aplikacja oczekuje pliku CSV z następującymi kolumnami:

```csv
data,opis,kwota,saldo
2024-01-15,Biedronka - zakupy,-50.00,1000.00
2024-01-14,Orlen - paliwo,-100.00,1050.00
2024-01-13,Rossmann - chemia,-30.00,1150.00
```

## 🏷️ Kategorie wydatków

Aplikacja automatycznie przypisuje transakcje do kategorii na podstawie opisu:

- **jedzenie** - Biedronka, Carrefour, Lidl, restauracje, etc.
- **chemia** - Rossmann, DM, apteki, etc.
- **paliwo** - Orlen, BP, Shell, stacje benzynowe
- **transport** - PKP, PKS, Uber, parkingi
- **rozrywka** - kino, teatr, Netflix, siłownia
- **rachunki** - PGE, woda, internet, telefon
- **zdrowie** - lekarz, szpital, leki
- **ubrania** - H&M, Zara, Reserved
- **inne** - transakcje niesklasyfikowane

## 🔮 Planowane funkcjonalności

- [ ] Porównania z poprzednimi tygodniami
- [ ] Wykresy wydatków według kategorii
- [ ] Trendy wydatków w czasie
- [ ] Alerty o przekroczeniu budżetu
- [ ] Eksport raportów do PDF
- [ ] API REST dla integracji z innymi aplikacjami
- [ ] Wsparcie dla różnych formatów bankowych

## 🧪 Testy

Uruchomienie testów:

```bash
python -m pytest tests/
```

lub

```bash
python tests/test_analyzer.py
```

## 🚀 Deployment

### Railway

Projekt jest skonfigurowany do wdrożenia na Railway:

1. Połącz repozytorium z Railway
2. Railway automatycznie wykryje `railway.json` i `Dockerfile`
3. Aplikacja zostanie wdrożona i będzie dostępna pod adresem URL

### Inne platformy

Aplikacja może być wdrożona na dowolnej platformie obsługującej Docker lub Python.

## 📝 Licencja

MIT License - zobacz plik LICENSE dla szczegółów.

## 🤝 Wkład

Zachęcamy do zgłaszania błędów i propozycji ulepszeń poprzez Issues na GitHub.

---

**Budget Control Web** - Kontroluj swoje wydatki z łatwością! 💰 