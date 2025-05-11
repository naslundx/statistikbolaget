import psycopg2
import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

# Global settings
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DB_URL = os.getenv("DB_URL")
app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def db_insert(command: str, data: tuple):
    conn = psycopg2.connect(DB_URL)

    try:
        cursor = conn.cursor()
        cursor.execute(command, data)
        conn.commit()

    except Exception as e:
        print(e)
        pass

    finally:
        conn.close()


def store_history(uuid, success, statement, sql, result):
    db_insert(
        "INSERT INTO history(uuid, success, statement, sql, result) VALUES (%s, %s, %s, %s, %s);",
        (uuid, success, statement, sql, result)
    )


def store_vote(_uuid: str, upvote: bool):
    print('vote', _uuid, upvote)
    if upvote:
        db_insert("UPDATE history SET upvote = upvote + 1 WHERE uuid = %s", (_uuid, ))
    else:
        db_insert("UPDATE history SET downvote = downvote + 1 WHERE uuid = %s", (_uuid, ))


# Start page
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("app/templates/index.html", encoding="utf-8") as f:
        return f.read()


class UserQuery(BaseModel):
    question: str


class VoteQuery(BaseModel):
    uuid: uuid.UUID
    upvote: bool


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

Och en query i en Postgres-databas har genererat svaret:
    {answer}

Omformulera svaret så att det blir mer människovänligt.
Ändra inga detaljer, men avrunda siffror eller formatera där det behövs.
Inkludera enheter på siffror.
Radbryt mellan punkter i en numrerad lista.
Lägg inte till ny information.

Om en tabell passar, inkludera den som html (<table>), inga css eller klasser.
I så fall, skriv inte samma fakta i plaintext.
"""
    result = send_to_openai(prompt)
    result = result.replace('`', '').replace('html', '')
    return result

def generate_sql(natural_question):
    prompt = f"""
Du är en SQL-assistent. Omvandla frågan till giltig SQL för en postgres-databas. Avsluta med semikolon.

# Tabeller (databas schema)

CREATE TABLE varugrupp (
    id INTEGER PRIMARY KEY,
    namn TEXT UNIQUE
)

CREATE TABLE varugrupp_detalj (
    id INTEGER PRIMARY KEY,
    namn TEXT UNIQUE
)

CREATE TABLE land (
    id INTEGER PRIMARY KEY,
    namn TEXT UNIQUE
)

CREATE TABLE region (
    id INTEGER PRIMARY KEY,
    namn TEXT UNIQUE
)

CREATE TABLE data (
    artnr TEXT,  -- systembolagets artikelnummer
    varunr TEXT,
    kvittonamn TEXT,
    namn TEXT,
    producentnamn TEXT,
    rubrik TEXT,
    aktuellt_pris REAL, -- pris per enhet i kronor
    volym_ml REAL, -- volym i milliliter per enhet
    buteljtyp TEXT,
    ursprung TEXT,
    fors_liter REAL, -- total försäljningsvolym
    artikel_id TEXT,
    varugrupp_id INTEGER,
    detalj_id INTEGER,
    land_id INTEGER,
    region_id INTEGER,
    ar_ekologisk BOOLEAN,
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
- Använd hellre ILIKE och procenttecken än exakt strängmatchning. Case insensitivity always!
- Sök om möjligt helst på varugrupp och i andra hand även varugrupp_detalj.
- Sök bara på innehåll i varans namn om inget annat går eller användaren explicit ber om det.
- Du får bara generera SELECT-kommandon och returnera endast SQL.
- Om du inte förstår, returnera "Förstår ej."
- All data är från år 2024.
- Begränsa (LIMIT) alltid data till max 50 rader (eller mindre om användaren ber om det).

Fråga: "{natural_question}"
SQL:
"""
    raw_data = send_to_openai(prompt)
    return extract_sql(raw_data)

def run_sql_query(sql: str):
    if not sql or 'SELECT' not in sql:
        return False, ""

    conn = psycopg2.connect(DB_URL)

    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        raw_result = cursor.fetchall()[:20]
        return True, raw_result

    except Exception as e:
        return False, str(e)

    finally:
        conn.close()


@app.post("/vote")
async def vote_api(data: VoteQuery):
    store_vote(str(data.uuid), data.upvote)
    return Response()


@app.post("/query")
async def query_api(data: UserQuery):
    question = data.question[:100]
    sql = generate_sql(question)
    success, raw_result = run_sql_query(sql)
    _uuid = str(uuid.uuid4())

    content = {
        "question": data.question,
        "sql": sql,
        "raw_result": raw_result,
        "success": success,
        "result": "",
        "uuid": _uuid,
    }

    if success:
        result = format_response(question, raw_result)
        content["result"] = result
        store_history(_uuid, success, question, sql, result)
    else:
        store_history(_uuid, success, question, sql, "")

    return JSONResponse(content=content)
