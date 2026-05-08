# 社交平台自动发布模块原理文档

## 概述

AI 日报 pipeline 在生成图片后，自动将图片上传到小红书和抖音的草稿箱，由用户手动确认后发布。两个平台都没有官方发布 API，因此采用不同的技术方案实现。

## 架构

```
Pipeline (jobs.py)
    ↓ 生成图片完成
    ├── XhsPublisher (小红书)
    │   └── xhs 库 → 创作者平台内部 API
    └── DouyinPublisher (抖音)
        └── Playwright → 浏览器自动化 → creator.douyin.com
```

## 小红书发布原理

### 技术方案

使用开源库 [xhs](https://github.com/ReaJason/xhs)（`pip install xhs`），它封装了小红书创作者平台的内部 API。

### 核心流程

1. **Cookie 认证**：用户从浏览器登录 `creator.xiaohongshu.com` 后，复制完整 Cookie 字符串
2. **初始化客户端**：`XhsClient(cookie=cookie_str)` 创建客户端实例
3. **上传图片笔记**：调用 `create_image_note()` 方法
   - `title`：笔记标题（格式：`AI日报 YYYY-MM-DD`）
   - `desc`：笔记描述（使用 LLM 生成的趋势总结）
   - `files`：图片文件路径列表
   - `is_private=True`：设置为仅自己可见（草稿模式）

### xhs 库内部原理

```
XhsClient
  ├── 解析 Cookie 获取 a1、web_session 等关键字段
  ├── 生成 X-s、X-t 签名（模拟前端加密逻辑）
  ├── POST /api/sns/web/v1/feed 上传图片
  └── POST /api/sns/web/v1/note 创建笔记
```

xhs 库通过逆向小红书前端 JS 的签名算法（xs/xt），在每次请求时生成合法的签名头，从而绕过接口校验。`is_private=True` 参数会将笔记设置为"仅自己可见"，等效于草稿。

### 关键代码

```python
from xhs import XhsClient

client = XhsClient(cookie="your_cookie_string")
client.create_image_note(
    title="AI日报 2026-05-08",
    desc="今日AI趋势：大模型竞争加剧...",
    files=["/path/to/daily_image.png"],
    is_private=True,  # 仅自己可见 = 草稿
)
```

## 抖音发布原理

### 技术方案

使用 [Playwright](https://playwright.dev/python/) 浏览器自动化框架，模拟真人操作抖音创作者中心。

### 为什么不用 API

抖音在 2024 年 7 月永久关闭了第三方"代投稿"API（原抖音开放平台视频发布接口），因此只能通过浏览器自动化方式实现。

### 核心流程

```
1. 解析 Cookie 字符串 → [{name, value, domain, path}]
2. 启动 Headless Chromium 浏览器
3. 创建浏览器上下文，注入 Cookie
4. 导航到 creator.douyin.com/creator-micro/content/upload
5. 触发文件选择器 → 上传图片文件
6. 填写标题输入框
7. 点击"存草稿"按钮
8. 关闭浏览器
```

### Cookie 解析

从浏览器复制的 Cookie 是分号分隔的字符串格式：
```
uid=123; sessionid=abc; token=xyz
```

解析为 Playwright 需要的结构：
```python
[
    {"name": "uid", "value": "123", "domain": ".douyin.com", "path": "/"},
    {"name": "sessionid", "value": "abc", "domain": ".douyin.com", "path": "/"},
    ...
]
```

### Playwright 自动化关键步骤

```python
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    context = await browser.new_context()
    await context.add_cookies(parsed_cookies)  # 注入登录态
    page = await context.new_page()
    
    await page.goto(upload_url, wait_until="networkidle")
    
    # 文件上传：通过 file chooser 事件
    async with page.expect_file_chooser() as fc_info:
        await page.click('div[class*="upload"]')  # 点击上传区域触发
    file_chooser = await fc_info.value
    await file_chooser.set_files(image_path)  # 设置文件
    
    # 填写标题、保存草稿
    await title_input.fill(title)
    await draft_btn.click()
```

`expect_file_chooser()` 是 Playwright 的关键 API——它监听浏览器的文件选择器弹窗事件，在点击上传按钮后拦截弹窗并自动填入文件路径，无需 GUI 交互。

## Pipeline 集成

在 `app/scheduler/jobs.py` 的 `run_daily_pipeline()` 函数末尾（保存报告之后）：

```python
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
```

**设计要点**：
- 仅在 `image_path` 非空时尝试上传（图片生成成功才上传）
- 仅在对应 Cookie 环境变量存在时才初始化发布器
- 上传失败不会阻塞 pipeline（异常在各发布器内部捕获并记录日志）
- 小红书使用同步调用（xhs 库是同步的），抖音使用异步调用（Playwright 是异步的）

## 配置说明

### 环境变量

| 变量 | 说明 | 获取方式 |
|------|------|----------|
| `XHS_COOKIE` | 小红书 Cookie | 登录 creator.xiaohongshu.com → F12 → Application → Cookies → 复制所有 |
| `DOUYIN_COOKIE` | 抖音 Cookie | 登录 creator.douyin.com → F12 → Application → Cookies → 复制所有 |

### Cookie 有效期

- **小红书**：约 30 天，过期后需重新登录获取
- **抖音**：有效期不固定，建议定期更新

### 风险提示

两个平台都是通过非官方方式实现，存在一定风险：
- Cookie 可能随时失效
- 平台可能更新页面结构导致自动化脚本失效（抖音）
- 频繁操作可能触发风控
- 上传草稿比直接发布的风控风险更低

## 依赖

```
xhs==0.2.13        # 小红书内部 API 封装
playwright>=1.59.0  # 浏览器自动化框架
```

首次使用抖音发布需要安装 Chromium 浏览器：
```bash
playwright install chromium
```
