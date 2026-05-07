import pytest
import sqlite3
from datetime import datetime
from app.models import NewsItem, DailyReport, init_db, save_report, get_latest_reports


def test_news_item_creation():
    item = NewsItem(
        title="GPT-5 Released",
        url="https://example.com/gpt5",
        source="hackernews",
        published_at=datetime(2026, 5, 7, 10, 0, 0),
        score=100,
        summary="OpenAI releases GPT-5",
    )
    assert item.title == "GPT-5 Released"
    assert item.source == "hackernews"


def test_daily_report_creation():
    report = DailyReport(
        date="2026-05-07",
        news_items=[],
        summary="Today in AI...",
        image_path="output/2026-05-07.png",
    )
    assert report.date == "2026-05-07"
    assert report.image_path == "output/2026-05-07.png"


def test_init_db_creates_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    assert "reports" in tables
    assert "news_items" in tables


def test_save_and_get_report(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    report = DailyReport(
        date="2026-05-07",
        news_items=[
            NewsItem(
                title="Test News",
                url="https://example.com",
                source="hackernews",
                published_at=datetime(2026, 5, 7, 10, 0, 0),
                score=50,
                summary="A test",
            )
        ],
        summary="Summary",
        image_path="output/2026-05-07.png",
    )
    save_report(db_path, report)
    reports = get_latest_reports(db_path, limit=5)
    assert len(reports) == 1
    assert reports[0].date == "2026-05-07"
