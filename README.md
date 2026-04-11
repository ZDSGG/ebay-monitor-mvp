# eBay 商品监控系统 MVP

当前版本已完成 MVP 全部 6 个阶段，并已在本机完成真实联调验证。

已完成：

- 阶段1：项目初始化、数据库连接、表创建、URL 解析
- 阶段2：eBay API 封装、新增商品、首次抓取
- 阶段3：snapshot 入库、列表接口
- 阶段4：定时任务、diff 分析、事件表
- 阶段5：前端页面、图表
- 阶段6：Excel 导出、CSV 导入、交付收尾

## 1. 技术栈

- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic
- APScheduler
- httpx
- PostgreSQL
- React
- Vite
- Recharts
- pandas
- openpyxl

## 2. 项目结构

```text
ebay_monitor_mvp/
├─ backend/
│  ├─ app/
│  │  ├─ api/routes/
│  │  ├─ core/
│  │  ├─ models/
│  │  ├─ schemas/
│  │  └─ services/
│  └─ scripts/
├─ frontend/
├─ sample_data/
├─ scripts/
├─ docs/
└─ .env.example
```

## 3. 核心功能

已实现：

- 商品录入
- eBay OAuth token 获取
- eBay Browse API 抓取
- snapshot 历史保存
- 昨日 / 周变化分析
- item events 写入
- APScheduler 定时抓取
- 商品列表页
- 新增商品页
- 商品详情页
- 30 天价格折线图
- CSV 导入
- Excel 导出

## 4. 数据库表

已创建：

- `monitored_items`
- `item_snapshots`
- `item_events`
- `crawl_jobs`

所有时间字段按 UTC 处理。

## 5. API 接口

### 系统

- `GET /api/health`
- `POST /api/utils/parse-ebay-url`

### 商品

- `POST /api/items`
- `GET /api/items`
- `GET /api/items/{item_id}`
- `POST /api/items/import-csv`

### 报表

- `GET /api/reports/items/{id}/export`

## 6. eBay OAuth 标准

当前 token 获取已按 Production 标准实现：

- URL:
  - `https://api.ebay.com/identity/v1/oauth2/token`
- Header:
  - `Content-Type: application/x-www-form-urlencoded`
  - `Authorization: Basic base64(client_id:client_secret)`
- Body:
  - `grant_type=client_credentials`
  - `scope=https://api.ebay.com/oauth/api_scope`

调试脚本：

- `backend/scripts/test_ebay_token.py`

## 7. 本机运行方式

### 7.1 初始化后端依赖

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 7.2 初始化数据库

如果首次运行：

```powershell
cd backend
set PYTHONPATH=.
python scripts/init_db.py
```

导入示例数据：

```powershell
C:\Users\Administrator\Documents\New project\ebay_monitor_mvp\postgresql-binaries\pgsql\bin\psql.exe -h 127.0.0.1 -p 5432 -U postgres -d ebay_monitor -f backend\scripts\seed_sample_data.sql
```

## 8. 一键启动脚本

### 启动全部服务

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\Documents\New project\ebay_monitor_mvp\scripts\start_all_dev.ps1
```

### 停止全部服务

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\Documents\New project\ebay_monitor_mvp\scripts\stop_all_dev.ps1
```

### 单独启动 PostgreSQL

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\Documents\New project\ebay_monitor_mvp\scripts\start_postgres_dev.ps1
```

### 单独停止 PostgreSQL

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\Documents\New project\ebay_monitor_mvp\scripts\stop_postgres_dev.ps1
```

### 单独启动后端

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\Documents\New project\ebay_monitor_mvp\backend\scripts\start_backend_dev.ps1
```

### 单独启动前端

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\Documents\New project\ebay_monitor_mvp\frontend\start_frontend_dev.ps1
```

## 9. 访问地址

- 前端：
  - `http://127.0.0.1:5173`
- 后端：
  - `http://127.0.0.1:8000`
- Swagger：
  - `http://127.0.0.1:8000/docs`
- ReDoc：
  - `http://127.0.0.1:8000/redoc`

## 10. 环境变量

根目录 `.env` 需包含：

- `DATABASE_URL`
- `EBAY_CLIENT_ID`
- `EBAY_CLIENT_SECRET`
- `EBAY_API_BASE_URL`
- `EBAY_AUTH_BASE_URL`
- `EBAY_OAUTH_SCOPE`

示例见：

- `.env.example`

## 11. 已验证结果

本机已验证：

- PostgreSQL 可启动
- 后端可启动
- 前端可启动
- eBay Production OAuth 可成功取 token
- `POST /api/items` 可真实抓取 eBay 商品
- snapshot 可入库
- 列表和详情接口可返回真实数据
- 前端页面可真实提交新增商品
- Excel 导出可返回文件
- CSV 导入可执行

## 12. 交付清单

已提供：

- 可运行项目
- README
- `.env.example`
- 数据库初始化脚本
- 示例数据
- API 文档
