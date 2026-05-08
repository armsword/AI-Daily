import logging
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import AppConfig
from app.crawler.hackernews import HackerNewsCrawler
from app.crawler.reddit import RedditCrawler
from app.analyzer.llm_analyzer import LLMAnalyzer
import os
from app.renderer.image_generator import NanoBananaImageGenerator
from app.publisher.xiaohongshu import XhsPublisher
from app.publisher.douyin import DouyinPublisher
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

    # 3. 构建报告（LLM分析后的新闻带有category和summary）
    today = date.today().isoformat()
    analyzed_items = []
    for n in analysis.categorized_news:
        # 从unique_news中找到对应的原始item补充时间等字段
        original = next((i for i in unique_news if i.url == n.get("url")), None)
        analyzed_items.append(NewsItem(
            title=n.get("title", ""),
            url=n.get("url", ""),
            source=n.get("source", ""),
            published_at=original.published_at if original else date.today(),
            score=original.score if original else 0,
            summary=n.get("summary", ""),
            category=n.get("category", "未分类"),
        ))

    # 4. 生成日报信息图（Nano Banana Pro via Visionary）
    image_path = ""
    api_key = os.environ.get("VISIONARY_API_KEY", "")
    if api_key:
        generator = NanoBananaImageGenerator(api_key=api_key)
        image_path = await generator.generate_daily_image(
            date=today,
            analysis=analysis,
            output_dir=config.output.dir,
        )

    # 5. 保存报告
    report = DailyReport(
        date=today,
        news_items=analyzed_items,
        summary=analysis.trend_summary,
        image_path=image_path,
    )
    save_report(DB_PATH, report)
    logger.info(f"Daily report saved: {today}")

    # 6. 上传到社交平台草稿
    if image_path:
        xhs_cookie = os.environ.get("XHS_COOKIE", "")
        if xhs_cookie:
            xhs_publisher = XhsPublisher(cookie=xhs_cookie)
            xhs_publisher.publish_draft(image_path, f"AI日报 {today}", analysis.trend_summary)

        douyin_cookie = os.environ.get("DOUYIN_COOKIE", "")
        if douyin_cookie:
            douyin_publisher = DouyinPublisher(cookie=douyin_cookie)
            await douyin_publisher.publish_draft(image_path, f"AI日报 {today}")


def create_daily_job(scheduler: AsyncIOScheduler, config: AppConfig) -> None:
    cron_parts = config.schedule.cron.split()
    trigger = CronTrigger(
        minute=cron_parts[0], hour=cron_parts[1],
        day=cron_parts[2], month=cron_parts[3], day_of_week=cron_parts[4],
    )
    scheduler.add_job(run_daily_pipeline, trigger, args=[config], id="daily_pipeline")
    logger.info(f"Scheduled daily job with cron: {config.schedule.cron}")
