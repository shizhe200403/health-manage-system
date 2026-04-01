# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目背景

本项目是一个**基于 Python 的智能菜谱推荐与营养健康管理系统**，作者的本科毕业设计，目前处于开发初期阶段，功能尚不完善，需持续优化改进。

系统核心目标：以用户健康档案为基础，综合运用协同过滤算法和内容推荐算法，提供个性化菜谱推荐，并整合营养分析、饮食记录、健康目标管理、数据可视化等功能，构建一站式营养健康管理平台。

开题报告详见 `requirments.md`。

## 部署信息

- **GitHub 仓库**：`shizhe200403/health-manage-system`
- **阿里云服务器**：华东1（杭州），Ubuntu 22.04，2核2GiB，公网IP `121.41.102.152`，开放 80/443/22 端口
- **服务器项目目录**：`/root/health-manage-system`
- **部署流程**：本地推送到 GitHub → 服务器拉取最新代码 → 重新部署

## 常用命令

```bash
# 开发环境（Docker）
make docker-up       # 启动所有服务
make docker-down     # 停止所有服务
make migrate         # 在运行中的容器内执行数据库迁移
make superuser       # 创建 Django 超级用户
make test            # 运行后端测试
make check           # 语法检查所有后端 Python 文件

# 生产环境
make prod-build      # 构建镜像
make prod-recreate   # 重建并重启 backend/worker/beat/frontend
make prod-migrate    # 生产环境执行迁移
make prod-health     # 验证 /healthz 和 /api/v1/health/
make prod-logs svc=backend  # 查看指定服务日志

# 前端（在 frontend/ 目录下）
npm run dev          # Vite 开发服务器
npm run build        # 生产构建
```

## 架构概览

**技术栈**：Django 5.2 + DRF 后端，Vue 3 + TypeScript + Vite 前端，PostgreSQL，Redis，Celery。

**请求链路**：浏览器 → Nginx（80端口）→ `/api/*` 反向代理到 Gunicorn（8000端口）；其余路径由 Vue SPA 静态文件处理。

**后端应用**（`backend/apps/`）：
- `accounts` — 自定义用户模型、JWT 认证、健康档案
- `recipes` — 菜谱与食材管理、营养摘要
- `tracking` — 饮食/餐食记录
- `nutrition` — 营养分析
- `recommendation` — 菜谱推荐引擎（协同过滤 + 内容推荐混合策略）
- `community` — 帖子、评论、内容审核
- `reports` — 周报/月报、PDF 导出（reportlab）
- `common` — 公共工具、健康检查、行为分析
- `external` — 外部开放平台数据代理

所有 API 路由前缀为 `/api/v1/`，OpenAPI Schema 在 `/api/schema/`，Swagger UI 在 `/api/docs/`。

**前端**（`frontend/src/`）：视图与功能模块一一对应，单一 Pinia store（`auth.ts`）管理 JWT Token，`api/` 目录结构与后端应用对应。

**异步任务**：Celery Worker 处理异步任务（推荐预计算、PDF 生成、图片处理），Celery Beat 处理定时任务，Redis 同时作为 Broker 和结果后端。

## 环境配置

复制 `.env.example` → `.env` 用于本地开发。若未设置 `DB_NAME` 环境变量，Django 会自动回退到 SQLite（无需 Docker 即可运行后端）。生产环境使用 `.env.production`（模板：`.env.production.example`）。

关键环境变量：`DJANGO_SECRET_KEY`、`DB_*`（PostgreSQL）、`REDIS_URL`、`CORS_ALLOWED_ORIGINS`、`SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE`（生产环境需设为 `true`）。
