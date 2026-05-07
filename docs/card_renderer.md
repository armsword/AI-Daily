# 卡片渲染模块原理文档

## 概述

卡片渲染模块负责将 LLM 分析结果（`AnalysisResult`）转换为一张精美的 PNG 图片卡片，用于社交媒体分享或日报展示。

## 架构设计

```
AnalysisResult -> render_html() -> HTML字符串 -> render_card() -> PNG文件
```

整个流程分为两步：
1. **HTML 渲染**：使用 Jinja2 模板引擎将数据填充到 HTML 模板中
2. **截图生成**：使用 html2image（底层调用 Chromium 无头浏览器）将 HTML 渲染为 PNG 图片

## 核心组件

### CardRenderer 类

```python
class CardRenderer:
    def __init__(self, output_dir: str, card_width: int = 800)
    def render_html(self, date: str, analysis: AnalysisResult) -> str
    def render_card(self, date: str, analysis: AnalysisResult) -> str
```

- `output_dir`：输出目录路径，PNG 文件将保存到此目录
- `card_width`：卡片宽度（像素），默认 800px

### HTML 模板（daily_card.html）

使用 Jinja2 模板语法，模板包含：
- **Header**：标题 "AI Daily" + 日期
- **Summary**：趋势总结（来自 `AnalysisResult.trend_summary`）
- **分类新闻列表**：按 category 分组展示新闻条目
- **Footer**：服务署名

样式采用深色主题（暗紫蓝渐变背景 + 青色强调色 `#64ffda`）。

## 数据流转

1. `render_html()` 接收日期和 `AnalysisResult`
2. 将 `categorized_news` 列表按 `category` 字段分组（使用 `defaultdict`）
3. 传入 Jinja2 模板进行渲染，生成完整 HTML 字符串
4. `render_card()` 调用 `render_html()` 获取 HTML
5. 使用 `Html2Image` 库启动无头 Chromium 浏览器
6. 对 HTML 进行截图，保存为 `{date}.png`

## 依赖库

| 库 | 用途 |
|---|---|
| jinja2 | HTML 模板渲染引擎 |
| html2image | HTML 转 PNG 截图工具 |

### html2image 工作原理

`html2image` 底层使用 Chromium/Chrome 浏览器的无头模式（headless mode）：

1. 启动一个无头 Chrome 进程
2. 加载 HTML 内容到浏览器页面
3. 设置视口大小为指定的 `size`（宽 x 高）
4. 使用 Chrome DevTools Protocol 截取页面截图
5. 保存截图为 PNG 文件

这意味着运行环境需要安装 Chrome 或 Chromium 浏览器。

## 模板变量

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `date` | str | 日期字符串，如 "2026-05-07" |
| `trend_summary` | str | AI 趋势总结文本 |
| `grouped_news` | dict[str, list[dict]] | 按分类分组的新闻列表 |
| `card_width` | int | 卡片宽度（CSS 中使用） |

## 注意事项

- 生成 PNG 需要系统安装 Chrome/Chromium 浏览器
- 卡片高度设为 1200px（固定截图区域），实际内容可能更短
- 输出目录不存在时会自动创建
