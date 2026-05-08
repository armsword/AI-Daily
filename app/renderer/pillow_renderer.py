import logging
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.analyzer.llm_analyzer import AnalysisResult

logger = logging.getLogger(__name__)

# 牛皮纸背景色 — 更暖更深，接近 gpt.jpg
BG_COLOR = (235, 222, 195)
BG_EDGE = (220, 205, 175)
# 文字颜色
TITLE_COLOR = (60, 35, 10)
TEXT_COLOR = (50, 40, 30)
LIGHT_TEXT = (120, 100, 75)
HIGHLIGHT_COLOR = (200, 80, 30)
# 分类标签颜色 — 更鲜明
CATEGORY_COLORS = {
    "大模型": (230, 126, 34),
    "应用": (41, 128, 185),
    "研究": (142, 68, 173),
    "开源": (39, 174, 96),
    "行业": (211, 84, 0),
    "融资并购": (211, 84, 0),
    "未分类": (127, 140, 141),
}
CIRCLED_NUMS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"

FONT_PATHS = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]

WIDTH = 800
MARGIN = 45
CONTENT_W = WIDTH - 2 * MARGIN


def _find_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        if Path(path).exists():
            try:
                index = 0
                if bold and "PingFang" in path:
                    index = 8  # PingFang SC Semibold
                return ImageFont.truetype(path, size, index=index)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width:
            if current:
                lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def _draw_dashed_line(draw: ImageDraw.ImageDraw, x1: int, x2: int, y: int,
                      color: tuple, dash: int = 10, gap: int = 6, width: int = 1) -> None:
    x = x1
    while x < x2:
        draw.line([(x, y), (min(x + dash, x2), y)], fill=color, width=width)
        x += dash + gap


class PillowInfographicRenderer:
    def __init__(self):
        self.title_font = _find_font(52, bold=True)
        self.subtitle_font = _find_font(20)
        self.date_font = _find_font(22)
        self.news_title_font = _find_font(24, bold=True)
        self.news_body_font = _find_font(18)
        self.label_font = _find_font(15, bold=True)
        self.small_font = _find_font(14)
        self.num_font = _find_font(32, bold=True)
        self.tagline_font = _find_font(13)
        self.footer_font = _find_font(14)

    def _draw_background(self, img: Image.Image) -> None:
        draw = ImageDraw.Draw(img)
        # 渐变牛皮纸背景
        for y in range(img.height):
            ratio = y / img.height
            r = int(BG_COLOR[0] * (1 - ratio * 0.06) + BG_EDGE[0] * ratio * 0.06)
            g = int(BG_COLOR[1] * (1 - ratio * 0.06) + BG_EDGE[1] * ratio * 0.06)
            b = int(BG_COLOR[2] * (1 - ratio * 0.06) + BG_EDGE[2] * ratio * 0.06)
            draw.line([(0, y), (img.width, y)], fill=(r, g, b))

        # 纸张纹理噪点
        pixels = img.load()
        for _ in range(img.width * img.height // 6):
            x = random.randint(0, img.width - 1)
            y = random.randint(0, img.height - 1)
            r, g, b = pixels[x, y]
            delta = random.randint(-10, 10)
            pixels[x, y] = (
                max(0, min(255, r + delta)),
                max(0, min(255, g + delta)),
                max(0, min(255, b + delta)),
            )

        # 边缘暗角
        for x in range(img.width):
            for band in range(8):
                if band < img.height:
                    r, g, b = pixels[x, band]
                    d = (8 - band) * 3
                    pixels[x, band] = (max(0, r - d), max(0, g - d), max(0, b - d))
                    by = img.height - 1 - band
                    if by >= 0:
                        r, g, b = pixels[x, by]
                        pixels[x, by] = (max(0, r - d), max(0, g - d), max(0, b - d))

    def _draw_header(self, draw: ImageDraw.ImageDraw, date: str, analysis: AnalysisResult) -> int:
        y = 25

        # 左上角 tagline
        draw.text((MARGIN, y), "每天3分钟，掌握AI大事", font=self.tagline_font, fill=LIGHT_TEXT)

        # 右上角核心要点
        points = analysis.categorized_news[:3]
        py = 22
        for item in points:
            t = item.get("title", "")[:18]
            checkbox = f"☑ {t}"
            bbox = draw.textbbox((0, 0), checkbox, font=self.tagline_font)
            tw = bbox[2] - bbox[0]
            draw.text((WIDTH - MARGIN - tw, py), checkbox, font=self.tagline_font, fill=LIGHT_TEXT)
            py += 22

        y += 40

        # 大标题 AI日报
        title = "AI日报"
        bbox = draw.textbbox((0, 0), title, font=self.title_font)
        tw = bbox[2] - bbox[0]
        tx = (WIDTH - tw) // 2
        # 标题底部装饰线
        draw.text((tx, y), title, font=self.title_font, fill=TITLE_COLOR)
        y += 65

        # 日期
        bbox = draw.textbbox((0, 0), date, font=self.date_font)
        dw = bbox[2] - bbox[0]
        draw.text(((WIDTH - dw) // 2, y), date, font=self.date_font, fill=LIGHT_TEXT)
        y += 38

        # 今日概要框
        summary = analysis.trend_summary[:100]
        summary_text = f"  {summary}"
        # 画方框
        box_y = y
        lines = _wrap_text(draw, summary_text, self.subtitle_font, CONTENT_W - 20)
        box_h = len(lines) * 28 + 16
        draw.rounded_rectangle(
            [(MARGIN, box_y), (WIDTH - MARGIN, box_y + box_h)],
            radius=6, outline=(180, 160, 130), width=2,
        )
        for line in lines:
            draw.text((MARGIN + 10, y + 8), line, font=self.subtitle_font, fill=TEXT_COLOR)
            y += 28
        y += 28

        # 粗分隔线
        draw.line([(MARGIN, y), (WIDTH - MARGIN, y)], fill=(180, 155, 120), width=3)
        y += 20

        return y

    def _draw_news_item(self, draw: ImageDraw.ImageDraw, item: dict, index: int, y: int) -> int:
        category = item.get("category", "未分类")
        title = item.get("title", "")
        summary = item.get("summary", "")
        color = CATEGORY_COLORS.get(category, CATEGORY_COLORS["未分类"])

        # 大号编号
        num = CIRCLED_NUMS[index] if index < len(CIRCLED_NUMS) else str(index + 1)
        draw.text((MARGIN, y - 4), num, font=self.num_font, fill=TITLE_COLOR)

        # 分类标签
        label_x = MARGIN + 48
        bbox = draw.textbbox((0, 0), category, font=self.label_font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        pad_x, pad_y = 10, 5
        tag_rect = [
            (label_x, y),
            (label_x + lw + pad_x * 2, y + lh + pad_y * 2)
        ]
        draw.rounded_rectangle(tag_rect, radius=10, fill=color)
        draw.text((label_x + pad_x, y + pad_y - 1), category, font=self.label_font, fill=(255, 255, 255))

        # 标题 — 加粗深色
        title_y = y + lh + pad_y * 2 + 10
        title_lines = _wrap_text(draw, title, self.news_title_font, CONTENT_W - 60)
        for line in title_lines:
            draw.text((MARGIN + 15, title_y), line, font=self.news_title_font, fill=TITLE_COLOR)
            title_y += 32

        # 摘要
        if summary:
            summary_lines = _wrap_text(draw, summary, self.news_body_font, CONTENT_W - 60)
            for line in summary_lines:
                draw.text((MARGIN + 15, title_y), line, font=self.news_body_font, fill=TEXT_COLOR)
                title_y += 26

        title_y += 12

        # 虚线分隔
        _draw_dashed_line(draw, MARGIN, WIDTH - MARGIN, title_y, (190, 170, 140), dash=10, gap=6, width=1)
        title_y += 18

        return title_y

    def _draw_decorations(self, draw: ImageDraw.ImageDraw, height: int) -> None:
        # 左侧竖线装饰
        draw.line([(20, 100), (20, height - 80)], fill=(210, 190, 160), width=1)
        # 右侧竖线装饰
        draw.line([(WIDTH - 20, 100), (WIDTH - 20, height - 80)], fill=(210, 190, 160), width=1)

    def _draw_footer(self, draw: ImageDraw.ImageDraw, y: int, height: int) -> None:
        # 底部分隔线
        footer_y = height - 55
        draw.line([(MARGIN, footer_y), (WIDTH - MARGIN, footer_y)], fill=(180, 155, 120), width=2)

        footer = "AI日报 · 每日AI新闻速递"
        bbox = draw.textbbox((0, 0), footer, font=self.footer_font)
        fw = bbox[2] - bbox[0]
        draw.text(((WIDTH - fw) // 2, footer_y + 12), footer, font=self.footer_font, fill=LIGHT_TEXT)

        # 来源小字
        source = "Data from Hacker News & Reddit"
        bbox = draw.textbbox((0, 0), source, font=self.tagline_font)
        sw = bbox[2] - bbox[0]
        draw.text(((WIDTH - sw) // 2, footer_y + 32), source, font=self.tagline_font, fill=(160, 145, 120))

    def _calc_height(self, analysis: AnalysisResult) -> int:
        n = min(len(analysis.categorized_news), 8)
        return max(280 + n * 150 + 100, 900)

    def render(self, date: str, analysis: AnalysisResult, output_dir: str) -> str:
        height = self._calc_height(analysis)
        img = Image.new("RGB", (WIDTH, height), BG_COLOR)
        self._draw_background(img)
        draw = ImageDraw.Draw(img)

        y = self._draw_header(draw, date, analysis)

        for i, item in enumerate(analysis.categorized_news[:8]):
            y = self._draw_news_item(draw, item, i, y)

        # 如果实际内容超出估算高度，重新绘制
        if y + 80 > height:
            new_height = y + 100
            new_img = Image.new("RGB", (WIDTH, new_height), BG_COLOR)
            self._draw_background(new_img)
            new_draw = ImageDraw.Draw(new_img)
            y = self._draw_header(new_draw, date, analysis)
            for i, item in enumerate(analysis.categorized_news[:8]):
                y = self._draw_news_item(new_draw, item, i, y)
            self._draw_decorations(new_draw, new_height)
            self._draw_footer(new_draw, y, new_height)
            img = new_img
        else:
            self._draw_decorations(draw, height)
            self._draw_footer(draw, y, height)

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        filename = f"{date}.png"
        output_path = str(Path(output_dir) / filename)
        img.save(output_path, "PNG")
        logger.info(f"Infographic generated: {output_path}")
        return output_path
