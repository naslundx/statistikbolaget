import pandas as pd
import sqlite3

# --- Inställningar ---
CSV_FIL = "forsaljning.csv"
DB_FIL = "forsaljning.db"

# --- Ladda och förbered datan ---
df = pd.read_csv(CSV_FIL, sep=";", decimal=",", low_memory=False)

# Byt namn på kolumnerna till SQL-vänliga namn
df.columns = [
    "artnr", "varunr", "kvittonamn", "namn", "producentnamn",
    "varugrupp", "varugrupp_detalj", "rubrik", "aktuellt_pris",
    "volym_ml", "buteljtyp", "land", "region", "ursprung",
    "ekologisk", "etiskt", "fors_liter", "artikel_id"
]

# Konvertera numeriska kolumner till rätt typ
df["aktuellt_pris"] = df["aktuellt_pris"].astype(float)
df["volym_ml"] = df["volym_ml"].astype(float)
df["fors_liter"] = df["fors_liter"].astype(str).str.replace(",", ".").str.replace("(", "").str.replace(")", "").astype(float)

# Skapa uppslagstabeller (unika värden)
def skapa_uppslagstabell(df, kolumnnamn):
    return pd.DataFrame({kolumnnamn: sorted(df[kolumnnamn].dropna().unique())})

varugrupper = skapa_uppslagstabell(df, "varugrupp")
detaljer = skapa_uppslagstabell(df, "varugrupp_detalj")
lander = skapa_uppslagstabell(df, "land")
regioner = skapa_uppslagstabell(df, "region")

# Lägg till ID-kolumner i uppslagstabeller
for tabell in [varugrupper, detaljer, lander, regioner]:
    tabell["id"] = range(1, len(tabell) + 1)

# Slå ihop uppslagstabeller till huvuddata
df = df.merge(varugrupper, on="varugrupp", how="left").rename(columns={"id": "varugrupp_id"})
df = df.merge(detaljer, on="varugrupp_detalj", how="left").rename(columns={"id": "detalj_id"})
df = df.merge(lander, on="land", how="left").rename(columns={"id": "land_id"})
df = df.merge(regioner, on="region", how="left").rename(columns={"id": "region_id"})

# --- Skapa databas och skriv till SQLite ---
conn = sqlite3.connect(DB_FIL)
c = conn.cursor()

# Skapa uppslagstabeller
c.execute("""
CREATE TABLE IF NOT EXISTS varugrupp (
    id INTEGER PRIMARY KEY,
    namn TEXT UNIQUE
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS varugrupp_detalj (
    id INTEGER PRIMARY KEY,
    namn TEXT UNIQUE
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS land (
    id INTEGER PRIMARY KEY,
    namn TEXT UNIQUE
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS region (
    id INTEGER PRIMARY KEY,
    namn TEXT UNIQUE
)
""")

# Skapa huvudtabell
c.execute("""
CREATE TABLE IF NOT EXISTS forsaljning (
    artnr TEXT,
    varunr TEXT,
    kvittonamn TEXT,
    namn TEXT,
    producentnamn TEXT,
    rubrik TEXT,
    aktuellt_pris REAL,
    volym_ml REAL,
    buteljtyp TEXT,
    ursprung TEXT,
    ekologisk TEXT,
    etiskt TEXT,
    fors_liter REAL,
    artikel_id TEXT,
    varugrupp_id INTEGER,
    detalj_id INTEGER,
    land_id INTEGER,
    region_id INTEGER,
    FOREIGN KEY(varugrupp_id) REFERENCES varugrupp(id),
    FOREIGN KEY(detalj_id) REFERENCES varugrupp_detalj(id),
    FOREIGN KEY(land_id) REFERENCES land(id),
    FOREIGN KEY(region_id) REFERENCES region(id)
)
""")

# Skriv till tabeller
varugrupper[["id", "varugrupp"]].rename(columns={"varugrupp": "namn"}).to_sql("varugrupp", conn, if_exists="append", index=False)
detaljer[["id", "varugrupp_detalj"]].rename(columns={"varugrupp_detalj": "namn"}).to_sql("varugrupp_detalj", conn, if_exists="append", index=False)
lander[["id", "land"]].rename(columns={"land": "namn"}).to_sql("land", conn, if_exists="append", index=False)
regioner[["id", "region"]].rename(columns={"region": "namn"}).to_sql("region", conn, if_exists="append", index=False)

# Välj kolumner till huvudtabellen
huvud_kolumner = [
    "artnr", "varunr", "kvittonamn", "namn", "producentnamn", "rubrik", "aktuellt_pris",
    "volym_ml", "buteljtyp", "ursprung", "ekologisk", "etiskt", "fors_liter", "artikel_id",
    "varugrupp_id", "detalj_id", "land_id", "region_id"
]
df[huvud_kolumner].to_sql("forsaljning", conn, if_exists="append", index=False)

conn.commit()
conn.close()

print(f"Import klar. Datan finns nu i {DB_FIL}.")
