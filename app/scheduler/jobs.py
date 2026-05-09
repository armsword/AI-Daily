import logging
import re
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import AppConfig
from app.crawler.hackernews import HackerNewsCrawler
from app.crawler.reddit import RedditCrawler
from app.crawler.techcrunch import TechCrunchCrawler
from app.crawler.producthunt import ProductHuntCrawler
from app.crawler.github_trending import GitHubTrendingCrawler
from app.analyzer.llm_analyzer import LLMAnalyzer
import os
from app.renderer.image_generator import NanoBananaImageGenerator
from app.publisher.xiaohongshu import XhsPublisher
from app.publisher.douyin import DouyinPublisher
from app.publisher.weixin_channels import WeixinChannelsPublisher
from app.models import NewsItem, DailyReport, init_db, save_report

logger = logging.getLogger(__name__)
DB_PATH = "ai_daily.db"


def _normalize_title(title: str) -> set[str]:
    return set(re.sub(r'[^\w\s]', '', title.lower()).split())


def _is_title_duplicate(title: str, existing_titles: list[str], threshold: float = 0.7) -> bool:
    words = _normalize_title(title)
    if not words:
        return False
    for existing in existing_titles:
        existing_words = _normalize_title(existing)
        if not existing_words:
            continue
        overlap = len(words & existing_words) / min(len(words), len(existing_words))
        if overlap > threshold:
            return True
    return False


def _deduplicate(news: list) -> list:
    seen_urls = set()
    titles = []
    unique = []
    for item in news:
        if item.url in seen_urls:
            continue
        if _is_title_duplicate(item.title, titles):
            continue
        seen_urls.add(item.url)
        titles.append(item.title)
        unique.append(item)
    return unique


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
    tc_crawler = TechCrunchCrawler(max_items=config.crawler.max_items_per_source)
    ph_crawler = ProductHuntCrawler(
        token=os.environ.get("PRODUCTHUNT_TOKEN", ""),
        max_items=30,
    )
    gh_crawler = GitHubTrendingCrawler(
        token=os.environ.get("GITHUB_TOKEN", ""),
        max_items=30,
    )

    hn_news = await hn_crawler.crawl()
    reddit_news = await reddit_crawler.crawl()
    tc_news = await tc_crawler.crawl()
    ph_news = await ph_crawler.crawl()
    gh_news = await gh_crawler.crawl()
    all_news = hn_news + reddit_news + tc_news + ph_news + gh_news

    # 去重：URL + 标题相似度
    unique_news = _deduplicate(all_news)

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
            await xhs_publisher.publish_draft(image_path, f"AI日报 {today}", analysis.trend_summary)

        douyin_cookie = os.environ.get("DOUYIN_COOKIE", "")
        if douyin_cookie:
            douyin_publisher = DouyinPublisher(cookie=douyin_cookie)
            await douyin_publisher.publish_draft(image_path, f"AI日报 {today}")

        weixin_cookie = os.environ.get("WEIXIN_CHANNELS_COOKIE", "")
        if weixin_cookie:
            weixin_publisher = WeixinChannelsPublisher(cookie=weixin_cookie)
            await weixin_publisher.publish_draft(image_path, f"AI日报 {today}", analysis.trend_summary)


def create_daily_job(scheduler: AsyncIOScheduler, config: AppConfig) -> None:
    cron_parts = config.schedule.cron.split()
    trigger = CronTrigger(
        minute=cron_parts[0], hour=cron_parts[1],
        day=cron_parts[2], month=cron_parts[3], day_of_week=cron_parts[4],
    )
    scheduler.add_job(run_daily_pipeline, trigger, args=[config], id="daily_pipeline")
    logger.info(f"Scheduled daily job with cron: {config.schedule.cron}")
