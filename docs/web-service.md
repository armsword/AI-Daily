# Web 服务与 FastAPI 入口 - 实现原理

## 架构概览

Web 服务层是 AI Daily 的用户界面入口，基于 FastAPI 框架构建，提供：
1. HTML 页面渲染（展示日报卡片）
2. RESTful API（供前端或第三方消费）
3. 静态文件服务（输出的 PNG 图片）
4. 定时任务调度（lifespan 生命周期管理）

## 核心组件

### 1. FastAPI Lifespan（生命周期管理）

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    config = load_config(CONFIG_PATH)
    init_db(DB_PATH)
    create_daily_job(scheduler, config)
    scheduler.start()
    yield
    # 关闭时执行
    scheduler.shutdown()
```

**原理：** FastAPI 的 lifespan 是一个异步上下文管理器，`yield` 之前的代码在应用启动时执行，之后的代码在关闭时执行。这替代了旧版的 `on_event("startup")` / `on_event("shutdown")` 模式。

优势：
- 资源的创建和销毁在同一个函数中，逻辑更清晰
- 支持异步操作
- 可以共享启动时创建的资源

### 2. Jinja2 模板渲染

```python
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", context)
```

**原理：** Jinja2 是 Python 生态中最流行的模板引擎。FastAPI 通过 `Jinja2Templates` 类集成它：
- 模板文件放在 `templates/` 目录
- 使用 `{{ variable }}` 语法插入变量
- 使用 `{% if %}` / `{% for %}` 进行逻辑控制
- `TemplateResponse` 将渲染后的 HTML 作为 HTTP 响应返回

### 3. 静态文件挂载

```python
app.mount("/output", StaticFiles(directory="output"), name="output")
```

**原理：** `StaticFiles` 是 Starlette 提供的 ASGI 应用，专门用于高效地服务静态文件。挂载后，`/output/2025-01-01.png` 这样的 URL 会直接映射到 `output/2025-01-01.png` 文件。

### 4. API 端点设计

```python
@app.get("/api/reports")
async def api_reports():
    reports = get_latest_reports(DB_PATH, limit=30)
    return [{"date": r.date, "summary": r.summary, "image_path": r.image_path} for r in reports]
```

**原理：** FastAPI 自动将 Python 字典/列表序列化为 JSON 响应。返回类型推断让 OpenAPI 文档自动生成。

## 请求处理流程

```
用户请求 GET /
    -> FastAPI 路由匹配
    -> index() 处理函数
    -> get_latest_reports() 从 SQLite 读取数据
    -> Jinja2 渲染 index.html 模板
    -> 返回 HTML 响应

用户请求 GET /output/2025-01-01.png
    -> FastAPI 路由匹配到 mount
    -> StaticFiles 直接返回文件
```

## 前端展示原理

模板使用纯 CSS 实现暗色主题的卡片式布局：
- CSS Grid 实现历史日报的响应式网格
- `aspect-ratio` 保持图片比例一致
- `transform: translateY(-4px)` 实现悬浮效果
- 无 JavaScript 依赖，纯服务端渲染

## 测试策略

使用 `TestClient`（基于 httpx）进行同步测试，通过 `unittest.mock.patch` 隔离数据库依赖：

```python
with patch("app.main.get_latest_reports") as mock_get:
    mock_get.return_value = []
    response = client.get("/")
```

这样测试只验证 Web 层逻辑，不依赖真实数据库。
