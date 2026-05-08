from pathlib import Path
from pydantic import BaseModel
import yaml


class ScheduleConfig(BaseModel):
    cron: str


class LLMConfig(BaseModel):
    model: str
    api_key_env: str


class CrawlerConfig(BaseModel):
    sources: list[str]
    reddit_subreddits: list[str]
    keywords: list[str]
    max_items_per_source: int


class OutputConfig(BaseModel):
    dir: str
    card_width: int
    top_n: int


class MiniMaxConfig(BaseModel):
    api_key_env: str
    api_base: str = "https://api.minimaxi.com"


class AppConfig(BaseModel):
    schedule: ScheduleConfig
    llm: LLMConfig
    crawler: CrawlerConfig
    output: OutputConfig
    minimax: MiniMaxConfig | None = None


def load_config(path: str) -> AppConfig:
    config_path = Path(path)
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    return AppConfig(**data)
