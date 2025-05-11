import os
import psycopg2
from openai import OpenAI


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DB_URL = os.getenv("DB_URL")


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
