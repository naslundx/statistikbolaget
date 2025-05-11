# statistikbolaget

## Krav
Behöver data från systembolaget
Kör via script.py för att skapa en databas

## Kör
uv run uvicorn app.main:app

Linting: uv run ruff check

Använd uv run python -m sqlite3 forsaljning.db för att interagera.

TODO:
- Använd cache från tabellen
- Inkludera data från tidigare år
