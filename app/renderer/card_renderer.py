import logging
from pathlib import Path
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader
from html2image import Html2Image
from app.analyzer.llm_analyzer import AnalysisResult

logger = logging.getLogger(__name__)


class CardRenderer:
    def __init__(self, output_dir: str, card_width: int = 800):
        self.output_dir = output_dir
        self.card_width = card_width
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

    def render_html(self, date: str, analysis: AnalysisResult) -> str:
        template = self.env.get_template("daily_card.html")
        grouped_news = defaultdict(list)
        for item in analysis.categorized_news:
            grouped_news[item.get("category", "未分类")].append(item)

        html = template.render(
            date=date,
            trend_summary=analysis.trend_summary,
            grouped_news=dict(grouped_news),
            card_width=self.card_width,
        )
        return html

    def render_card(self, date: str, analysis: AnalysisResult) -> str:
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        html = self.render_html(date, analysis)
        filename = f"{date}.png"

        hti = Html2Image(output_path=self.output_dir, size=(self.card_width, 1200))
        hti.screenshot(html_str=html, save_as=filename)

        output_path = str(Path(self.output_dir) / filename)
        logger.info(f"Card generated: {output_path}")
        return output_path
