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

def format_response(natural_question, answer) -> str:
    prompt = f"""
En användare har ställt frågan:
    {natural_question}

Och ett datorsystem har genererat svaret:
    {answer}

Omformulera svaret så att det blir mer människovänligt. Ändra inga detaljer, men avrunda siffror eller formatera där det behövs.

Svar till användaren:
"""
    result = send_to_openai(prompt)
    return result

def generate_sql(natural_question):
    prompt = f"""
Du är en SQL-assistent. Omvandla frågan till giltig SQL för en SQLite3-databas. Avsluta med semikolon.

Tabellerna skapades såhär:

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

Tänk på att kolumnen namn finns i flera tabeller!
Använd hellre LIKE och procenttecken än exakt strängmatchning.
Sök om möjligt helst på varugrupp och i andra hand även varugrupp_detalj.
Sök bara på innehåll i varans namn om inget annat går eller användaren explicit ber om det.

Fråga: "{natural_question}"
SQL:
"""
    raw_data = send_to_openai(prompt)
    return raw_data.split(';')[0].replace('sql', '').replace('`', '')

@app.post("/query")
async def query_api(data: UserQuery):
    question = data.question[:100]
    sql = generate_sql(question)

    error_msg = ""
    result = ""
    raw_result = ""

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        raw_result = df.to_html(index=False)
        result = format_response(question, raw_result)
    except Exception as e:
        error_msg = str(e)

    return JSONResponse(content={
        "question": data.question,
        "sql": sql,
        "result": result,
        "raw_result": raw_result,
        "error_msg": error_msg,
    })
