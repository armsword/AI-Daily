import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.scheduler.jobs import create_daily_job, run_daily_pipeline
from app.config import load_config


def test_create_daily_job():
    config = load_config("config.yaml")
    scheduler = MagicMock()
    create_daily_job(scheduler, config)
    scheduler.add_job.assert_called_once()
    call_kwargs = scheduler.add_job.call_args
    assert call_kwargs is not None


@pytest.mark.asyncio
async def test_run_daily_pipeline():
    config = load_config("config.yaml")
    with patch("app.scheduler.jobs.HackerNewsCrawler") as mock_hn, \
         patch("app.scheduler.jobs.RedditCrawler") as mock_reddit, \
         patch("app.scheduler.jobs.TechCrunchCrawler") as mock_tc, \
         patch("app.scheduler.jobs.ProductHuntCrawler") as mock_ph, \
         patch("app.scheduler.jobs.GitHubTrendingCrawler") as mock_gh, \
         patch("app.scheduler.jobs.LLMAnalyzer") as mock_analyzer, \
         patch("app.scheduler.jobs.NanoBananaImageGenerator") as mock_generator, \
         patch("app.scheduler.jobs.XhsPublisher") as mock_xhs, \
         patch("app.scheduler.jobs.DouyinPublisher") as mock_douyin, \
         patch.dict("os.environ", {"VISIONARY_API_KEY": "test-key"}), \
         patch("app.scheduler.jobs.save_report") as mock_save, \
         patch("app.scheduler.jobs.init_db"):

        mock_hn_instance = AsyncMock()
        mock_hn_instance.crawl.return_value = []
        mock_hn.return_value = mock_hn_instance

        mock_reddit_instance = AsyncMock()
        mock_reddit_instance.crawl.return_value = []
        mock_reddit.return_value = mock_reddit_instance

        mock_tc_instance = AsyncMock()
        mock_tc_instance.crawl.return_value = []
        mock_tc.return_value = mock_tc_instance

        mock_ph_instance = AsyncMock()
        mock_ph_instance.crawl.return_value = []
        mock_ph.return_value = mock_ph_instance

        mock_gh_instance = AsyncMock()
        mock_gh_instance.crawl.return_value = []
        mock_gh.return_value = mock_gh_instance

        mock_analyzer_instance = AsyncMock()
        mock_analyzer_instance.analyze.return_value = MagicMock(
            trend_summary="test", categorized_news=[]
        )
        mock_analyzer.return_value = mock_analyzer_instance

        mock_gen_instance = AsyncMock()
        mock_gen_instance.generate_daily_image.return_value = "output/2026-05-07.png"
        mock_generator.return_value = mock_gen_instance

        await run_daily_pipeline(config)

        mock_hn_instance.crawl.assert_called_once()
        mock_reddit_instance.crawl.assert_called_once()
        mock_tc_instance.crawl.assert_called_once()
        mock_analyzer_instance.analyze.assert_called_once()
