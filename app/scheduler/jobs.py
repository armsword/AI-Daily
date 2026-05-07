import logging
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import AppConfig
from app.crawler.hackernews import HackerNewsCrawler
from app.crawler.reddit import RedditCrawler
from app.analyzer.llm_analyzer import LLMAnalyzer
from app.renderer.card_renderer import CardRenderer
from app.models import NewsItem, DailyReport, init_db, save_report

logger = logging.getLogger(__name__)
DB_PATH = "ai_daily.db"


async def run_daily_pipeline(config: AppConfig) -> None:
    logger.info("Starting daily pipeline...")
    init_db(DB_PATH)

    # 1. 爬取新闻
    hn_crawler = HackerNewsCrawler(
        keywords=config.crawler.keywords,
        max_items=config.crawler.max_items_per_source,
    )
    reddit_crawler = RedditCrawler(
        subreddits=config.crawler.reddit_subreddits,
        keywords=config.crawler.keywords,
        max_items=config.crawler.max_items_per_source,
    )

    hn_news = await hn_crawler.crawl()
    reddit_news = await reddit_crawler.crawl()
    all_news = hn_news + reddit_news

    # 去重
    seen_urls = set()
    unique_news = []
    for item in all_news:
        if item.url not in seen_urls:
            seen_urls.add(item.url)
            unique_news.append(item)

    logger.info(f"Collected {len(unique_news)} unique news items")

    # 2. LLM 分析
    analyzer = LLMAnalyzer(model=config.llm.model, top_n=config.output.top_n)
    analysis = await analyzer.analyze(unique_news)

    # 3. 渲染卡片
    today = date.today().isoformat()
    renderer = CardRenderer(output_dir=config.output.dir, card_width=config.output.card_width)
    image_path = renderer.render_card(today, analysis)

    # 4. 保存报告
    report = DailyReport(
        date=today,
        news_items=unique_news,
        summary=analysis.trend_summary,
        image_path=image_path,
    )
    save_report(DB_PATH, report)
    logger.info(f"Daily report saved: {today}")


def create_daily_job(scheduler: AsyncIOScheduler, config: AppConfig) -> None:
    cron_parts = config.schedule.cron.split()
    trigger = CronTrigger(
        minute=cron_parts[0], hour=cron_parts[1],
        day=cron_parts[2], month=cron_parts[3], day_of_week=cron_parts[4],
    )
    scheduler.add_job(run_daily_pipeline, trigger, args=[config], id="daily_pipeline")
    logger.info(f"Scheduled daily job with cron: {config.schedule.cron}")
