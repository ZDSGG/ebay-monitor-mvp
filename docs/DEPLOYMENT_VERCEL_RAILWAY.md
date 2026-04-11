# 部署方案：Vercel + Railway

目标：

- 前端部署到 Vercel，提供公开访问网址
- 后端部署到 Railway，由你托管
- PostgreSQL 部署到 Railway，由你托管
- eBay 凭证仅保存在 Railway 环境变量中

## 一、整体架构

- 前端：`frontend`
- 后端：`backend`
- 数据库：Railway PostgreSQL

访问方式：

- 用户只访问前端网址，例如 `https://your-project.vercel.app`
- 前端通过 `VITE_API_BASE_URL` 调用 Railway 上的 FastAPI

## 二、部署顺序

1. 把项目上传到 GitHub
2. 在 Railway 创建 PostgreSQL
3. 在 Railway 部署后端
4. 在 Vercel 部署前端
5. 在 Railway 配置 Cron Job

## 三、GitHub 准备

不要提交真实 `.env`。

保留这些文件：

- `.env.example`
- `backend/Procfile`
- `backend/runtime.txt`
- `frontend/vercel.json`

## 四、Railway 部署后端

### 1. 创建项目

在 Railway 新建项目，连接 GitHub 仓库。

### 2. 设置 Root Directory

后端服务的 Root Directory 设为：

```text
backend
```

### 3. 启动命令

如果 Railway 没自动识别 `Procfile`，手动填：

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 4. 环境变量

必须配置：

```text
APP_ENV=production
DEBUG=false
API_PREFIX=/api
CORS_ALLOW_ORIGINS=https://你的-vercel-域名
DATABASE_URL=Railway 提供的 PostgreSQL 连接串
TIMEZONE=UTC
EBAY_CLIENT_ID=你的 eBay Production Client ID
EBAY_CLIENT_SECRET=你的 eBay Production Client Secret
EBAY_MARKETPLACE_ID=EBAY_US
EBAY_API_BASE_URL=https://api.ebay.com
EBAY_AUTH_BASE_URL=https://api.ebay.com
EBAY_OAUTH_SCOPE=https://api.ebay.com/oauth/api_scope
EBAY_REQUEST_TIMEOUT_SECONDS=10
EBAY_MAX_RETRIES=3
ENABLE_SCHEDULER=false
CRON_SECRET=你自定义的一串高强度密钥
```

说明：

- 线上建议 `ENABLE_SCHEDULER=false`
- 定时抓取改由 Railway Cron Job 触发
- `CRON_SECRET` 用于保护内部抓取接口

### 5. 验证后端

部署成功后先打开：

- `/api/health`
- `/docs`

例如：

```text
https://your-backend.up.railway.app/api/health
https://your-backend.up.railway.app/docs
```

## 五、Railway PostgreSQL

在同一个 Railway 项目中添加 PostgreSQL。

把 Railway 生成的连接串填到后端环境变量：

```text
DATABASE_URL
```

## 六、Vercel 部署前端

### 1. 导入项目

在 Vercel 导入同一个 GitHub 仓库。

### 2. 设置 Root Directory

前端 Root Directory 设为：

```text
frontend
```

### 3. 环境变量

配置：

```text
VITE_API_BASE_URL=https://your-backend.up.railway.app/api
```

### 4. 路由说明

项目已提供：

- `frontend/vercel.json`

它会把所有前端路由重写到 `index.html`，避免直接访问 `/items` 或 `/items/:id` 时出现 404。

## 七、Railway Cron Job

为了让系统每天自动抓取商品，使用 Railway Cron Job 调用内部接口：

```text
POST /api/ops/run-daily-crawl
```

请求头：

```text
X-Cron-Secret: 你配置的 CRON_SECRET
```

示例：

```bash
curl -X POST "https://your-backend.up.railway.app/api/ops/run-daily-crawl" \
  -H "X-Cron-Secret: your-strong-secret"
```

建议每天 UTC 09:00 运行一次。

## 八、最终交付方式

部署完成后，你发给别人的是：

- 前端网址，例如 `https://your-project.vercel.app`

别人直接打开前端网址即可使用。

你自己负责托管：

- Railway 后端
- Railway PostgreSQL
- eBay API 凭证

## 九、上线前检查

- 前端 `VITE_API_BASE_URL` 指向线上后端
- 后端 `CORS_ALLOW_ORIGINS` 只允许你的 Vercel 域名
- `ENABLE_SCHEDULER=false`
- `CRON_SECRET` 已设置
- eBay 凭证仅存在 Railway 环境变量中
- GitHub 仓库没有上传真实 `.env`
