#!/bin/bash

# Ustaw domyślną wartość PORT jeśli nie jest ustawiona
export PORT=${PORT:-8000}

echo "Starting application on port $PORT"

# Uruchom aplikację
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT 