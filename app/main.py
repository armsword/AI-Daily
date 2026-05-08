import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import load_config, AppConfig
from app.models import init_db, get_latest_reports
from app.scheduler.jobs import create_daily_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

CONFIG_PATH = "config.yaml"
DB_PATH = "ai_daily.db"

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config(CONFIG_PATH)
    init_db(DB_PATH)
    Path(config.output.dir).mkdir(parents=True, exist_ok=True)
    create_daily_job(scheduler, config)
    scheduler.start()
    logger.info("AI Daily service started")
    yield
    scheduler.shutdown()


app = FastAPI(title="AI Daily", lifespan=lifespan)

Path("output").mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory="output"), name="output")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    reports = get_latest_reports(DB_PATH, limit=30)
    latest = reports[0] if reports else None
    history = reports[1:] if len(reports) > 1 else []
    return templates.TemplateResponse(request, "index.html", {
        "latest_report": latest,
        "history_reports": history,
    })


@app.get("/api/reports")
async def api_reports():
    reports = get_latest_reports(DB_PATH, limit=30)
    return [{"date": r.date, "summary": r.summary, "image_path": r.image_path} for r in reports]
