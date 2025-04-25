# statistikbolaget

## Krav
Behöver data från systembolaget
Kör via script.py för att skapa en databas

## Kör
uv run uvicorn main:app

Linting: uv run ruff check

Använd uv run python -m sqlite3 forsaljning.db för att interagera.

TODO:
- Designa history + error bars
- Max limit på data
- Formatera output/tabeller bättre
- Kontrollera select query + readonly user
- Tabell över sökningar + resultat
- Publicera

Framtid:
- Använd cache per query?
- Inkludera data från tidigare år
- Upvote/Downvote på resultatet
