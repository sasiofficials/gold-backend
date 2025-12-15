from fastapi import FastAPI
import requests
import sqlite3
from datetime import date
import os

API_KEY = os.getenv("GOLDAPI_KEY")   # replace this
HEADERS = {"x-access-token": API_KEY}
OZ_TO_GRAM = 31.1035

app = FastAPI()

conn = sqlite3.connect("gold.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS rates (
    date TEXT PRIMARY KEY,
    gold_24k REAL,
    gold_22k REAL,
    silver REAL
)
""")
conn.commit()

@app.get("/")
def health():
    return {"status": "running"}

@app.get("/rates/today")
def today_rates():
    today = str(date.today())

    cur.execute("SELECT * FROM rates WHERE date=?", (today,))
    row = cur.fetchone()

    if row:
        return {
            "date": row[0],
            "gold_24k": row[1],
            "gold_22k": row[2],
            "silver": row[3],
            "source": "cache"
        }

    gold = requests.get("https://www.goldapi.io/api/XAU/INR", headers=HEADERS).json()
    silver = requests.get("https://www.goldapi.io/api/XAG/INR", headers=HEADERS).json()

    gold_24k = gold["price"] / OZ_TO_GRAM
    gold_22k = gold_24k * 0.916
    silver_rate = silver["price"] / OZ_TO_GRAM

    cur.execute(
        "INSERT INTO rates VALUES (?,?,?,?)",
        (today, round(gold_24k, 2), round(gold_22k, 2), round(silver_rate, 2))
    )
    conn.commit()

    return {
        "date": today,
        "gold_24k": round(gold_24k, 2),
        "gold_22k": round(gold_22k, 2),
        "silver": round(silver_rate, 2),
        "source": "goldapi.io"
    }
