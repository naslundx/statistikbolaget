# statistikbolaget

## Krav
Behöver data från systembolaget
Kör via script.py för att skapa en databas

## Kör
uv run uvicorn main:app

Linting: uv run ruff check

Använd uv run python -m sqlite3 forsaljning.db för att interagera.

TODO:
- Designa error box
- Specifikt fel om db otillgänglig
- Max limit på data
- Readonly db user
- Tabell över sökningar + resultat

Framtid:
- Formatera output/tabeller bättre
- Använd cache per query?
- Inkludera data från tidigare år
- Upvote/Downvote på resultatet
