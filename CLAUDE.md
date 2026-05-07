# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
AI 日报自动化服务。每天定时从 Hacker News 和 Reddit 爬取 AI 新闻，通过 LLM 深度分析后生成日报卡片图片，通过 Web 页面展示。

技术栈：Python / FastAPI / APScheduler / litellm / html2image / SQLite


## Tasks
原子任务列表@tasks.md

## TDD
- 严格按照TDD测试驱动开发三条规则，每次只写一个失败测试，再写实现

## User
- 完成后每次回复我前，都要用 若飞 称呼我
- 每个功能完成（比如算子怎么实现）后需要编写一份详细的原理文档，放到docs目录里，方便我明白底层实现原理

## Git 工作流
- 每个功能/接口完成后立即 commit，不要等到全部写完
- Commit message 使用中文，格式：`[功能名] 简短描述`
- Commit 前确保测试通过
- commit完成后提交到远程分支
