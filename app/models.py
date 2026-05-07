import json
import sqlite3
from datetime import datetime
from pydantic import BaseModel


class NewsItem(BaseModel):
    title: str
    url: str
    source: str
    published_at: datetime
    score: int
    summary: str
    category: str = ""


class DailyReport(BaseModel):
    date: str
    news_items: list[NewsItem]
    summary: str
    image_path: str


def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            summary TEXT NOT NULL,
            image_path TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            source TEXT NOT NULL,
            published_at TEXT NOT NULL,
            score INTEGER NOT NULL,
            summary TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (report_date) REFERENCES reports(date)
        )
    """)
    conn.commit()
    conn.close()


def save_report(db_path: str, report: DailyReport) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO reports (date, summary, image_path) VALUES (?, ?, ?)",
        (report.date, report.summary, report.image_path),
    )
    conn.execute("DELETE FROM news_items WHERE report_date = ?", (report.date,))
    for item in report.news_items:
        conn.execute(
            """INSERT INTO news_items (report_date, title, url, source, published_at, score, summary, category)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (report.date, item.title, item.url, item.source,
             item.published_at.isoformat(), item.score, item.summary, item.category),
        )
    conn.commit()
    conn.close()


def get_latest_reports(db_path: str, limit: int = 30) -> list[DailyReport]:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT date, summary, image_path FROM reports ORDER BY date DESC LIMIT ?",
        (limit,),
    )
    reports = []
    for row in cursor.fetchall():
        date, summary, image_path = row
        items_cursor = conn.execute(
            "SELECT title, url, source, published_at, score, summary, category FROM news_items WHERE report_date = ?",
            (date,),
        )
        news_items = [
            NewsItem(
                title=r[0], url=r[1], source=r[2],
                published_at=datetime.fromisoformat(r[3]),
                score=r[4], summary=r[5], category=r[6],
            )
            for r in items_cursor.fetchall()
        ]
        reports.append(DailyReport(date=date, news_items=news_items, summary=summary, image_path=image_path))
    conn.close()
    return reports
