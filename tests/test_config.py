import pytest
from app.config import load_config, AppConfig


def test_load_config_returns_app_config():
    config = load_config("config.yaml")
    assert isinstance(config, AppConfig)


def test_config_schedule_cron():
    config = load_config("config.yaml")
    assert config.schedule.cron == "0 8 * * *"


def test_config_llm_model():
    config = load_config("config.yaml")
    assert "claude" in config.llm.model or "gpt" in config.llm.model


def test_config_crawler_sources():
    config = load_config("config.yaml")
    assert "hackernews" in config.crawler.sources
    assert "reddit" in config.crawler.sources


def test_config_output_dir():
    config = load_config("config.yaml")
    assert config.output.dir == "output"
