import sqlite3
import os
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

# Global settings
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DB_PATH = "forsaljning.db"
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Start page
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html", encoding="utf-8") as f:
        return f.read()


class UserQuery(BaseModel):
    question: str


def send_to_openai(prompt) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

    raw_data = response.choices[0].message.content.strip()
    return raw_data

def extract_sql(raw_response: str) -> str:
    start_index = raw_response.find("SELECT ");
    if start_index < 0:
        return ""
    end_index = raw_response.find(";", start_index + 1) + 1
    if end_index < 0:
        return ""

    return raw_response[start_index:end_index]

def format_response(natural_question, answer) -> str:
    prompt = f"""
En användare har ställt frågan:
    {natural_question}

Och ett datorsystem har genererat svaret:
    {answer}

Omformulera svaret så att det blir mer människovänligt.
Ändra inga detaljer, men avrunda siffror eller formatera där det behövs.
Inkludera enheter på siffror.
Radbryt mellan punkter i en numrerad lista.
Lägg inte till ny information.

Svar till användaren:
"""
    result = send_to_openai(prompt)
    return result

def generate_sql(natural_question):
    prompt = f"""
Du är en SQL-assistent. Omvandla frågan till giltig SQL för en SQLite3-databas. Avsluta med semikolon.

# Tabeller (databas schema)

CREATE TABLE IF NOT EXISTS varugrupp (
    id INTEGER PRIMARY KEY,
    namn TEXT UNIQUE
)

CREATE TABLE IF NOT EXISTS varugrupp_detalj (
    id INTEGER PRIMARY KEY,
    namn TEXT UNIQUE
)

CREATE TABLE IF NOT EXISTS land (
    id INTEGER PRIMARY KEY,
    namn TEXT UNIQUE
)

CREATE TABLE IF NOT EXISTS region (
    id INTEGER PRIMARY KEY,
    namn TEXT UNIQUE
)

CREATE TABLE IF NOT EXISTS forsaljning (
    artnr TEXT,  -- systembolagets artikelnummer
    varunr TEXT,
    kvittonamn TEXT,
    namn TEXT,
    producentnamn TEXT,
    rubrik TEXT,
    aktuellt_pris REAL,
    volym_ml REAL, -- volym i milliliter per enhet
    buteljtyp TEXT,
    ursprung TEXT,
    ar_ekologisk BOOLEAN,
    fors_liter REAL, -- total försäljningsvolym
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

Möjliga varugrupp: 'Alkoholfritt', 'Presentsortiment', 'Sprit', 'Vin', 'Öl, cider & blanddryck', 'Övrigt'.
Möjliga varugrupp_detalj: 'Alkoholfritt övrigt', 'Avec', 'Cider & spritdrycker', 'Drinkar & Cocktails', 'Lageröl', 'Mousserande vin', 'Presentsortiment', 'Rosévin', 'Rött vin', 'Snaps', 'Specialöl', 'Säsongscider & blanddrycker', 'Säsongssprit', 'Säsongsöl', 'Vitt vin', 'Whisky', 'okänt', 'Övrigt', 'Övrigt vin'.
Exempel på land: 'Argentina', 'Sverige', 'Frankrike'.
Exempel på region: 'Alsace', 'Western Australia', 'Gävleborgs län'.

# Regler:
- Tänk på att kolumnen namn finns i flera tabeller!
- Använd hellre LIKE och procenttecken än exakt strängmatchning.
- Sök om möjligt helst på varugrupp och i andra hand även varugrupp_detalj.
- Sök bara på innehåll i varans namn om inget annat går eller användaren explicit ber om det.
- All data är från år 2024.
- Du får bara generera SELECT-kommandon och returnera endast SQL.
- Om du inte förstår, returnera "Förstår ej."

Fråga: "{natural_question}"
SQL:
"""
    raw_data = send_to_openai(prompt)
    return extract_sql(raw_data)

def run_sql_query(sql: str):
    if not sql or 'SELECT' not in sql:
        return False, ""

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        raw_result = df.to_html(index=False)
        return True, raw_result

    except Exception as e:
        return False, str(e)

@app.post("/query")
async def query_api(data: UserQuery):
    question = data.question[:100]
    sql = generate_sql(question)
    success, raw_result = run_sql_query(sql)

    content = {
        "question": data.question,
        "sql": sql,
        "raw_result": raw_result,
        "success": success
    }

    if success:
        result = format_response(question, raw_result)
        content["result"] = result

    return JSONResponse(content=content)
