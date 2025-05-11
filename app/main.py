import psycopg2
import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .models import UserQuery, VoteQuery
from .external import db_insert, send_to_openai, run_sql_query
from .prompts import PROMPT_GENERATE_SQL, PROMPT_GENERATE_RESPONSE

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def store_history(uuid, ip, success, statement, sql, result):
    db_insert(
        "INSERT INTO history(uuid, ip, success, statement, sql, result) VALUES (%s, %s, %s, %s, %s);",
        (uuid, ip, success, statement, sql, result)
    )


def store_vote(_uuid: str, upvote: bool):
    if upvote:
        db_insert("UPDATE history SET upvote = upvote + 1 WHERE uuid = %s", (_uuid, ))
    else:
        db_insert("UPDATE history SET downvote = downvote + 1 WHERE uuid = %s", (_uuid, ))


def extract_sql(raw_response: str) -> str:
    start_index = raw_response.find("SELECT ");
    if start_index < 0:
        return ""
    end_index = raw_response.find(";", start_index + 1) + 1
    if end_index < 0:
        return ""

    return raw_response[start_index:end_index]


def format_response(natural_question, answer) -> str:
    prompt = PROMPT_GENERATE_RESPONSE.format(natural_question=natural_question, answer=answer)
    result = send_to_openai(prompt)
    result = result.replace('`', '').replace('html', '')
    return result


def generate_sql(natural_question):
    prompt = PROMPT_GENERATE_SQL.format(natural_question=natural_question)
    raw_data = send_to_openai(prompt)
    return extract_sql(raw_data)


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("app/templates/index.html", encoding="utf-8") as f:
        return f.read()


@app.post("/vote")
async def vote_api(data: VoteQuery):
    store_vote(str(data.uuid), data.upvote)
    return Response()


@app.post("/query")
async def query_api(data: UserQuery, request: Request):
    question = data.question[:100]
    sql = generate_sql(question)
    success, raw_result = run_sql_query(sql)
    _uuid = str(uuid.uuid4())
    ip = request.client.host

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
        store_history(_uuid, ip, success, question, sql, result)
    else:
        store_history(_uuid, ip, success, question, sql, "")

    return JSONResponse(content=content)
