import sqlite3
import pandas as pd

# Öppna databasen
conn = sqlite3.connect("forsaljning.db")
cursor = conn.cursor()

# Räkna antal rader i huvudtabellen
cursor.execute("SELECT COUNT(*) FROM forsaljning")
antal = cursor.fetchone()[0]
print(f"Antal rader i tabellen 'forsaljning': {antal}\n")

# Läs användarens SQL-fråga
while True:
    print("Skriv en SQL-fråga (t.ex. SELECT * FROM forsaljning LIMIT 5):")
    sql = input("SQL> ")

    if not sql:
        break

    try:
        df = pd.read_sql_query(sql, conn)
        if df.empty:
            print("\nInga rader matchade din fråga.")
        else:
            print("\nResultat:\n")
            print(df.to_string(index=False))
    except Exception as e:
        print(f"\nFel vid körning av SQL: {e}")

conn.close()
