# 上线操作清单

目标：

- 前端部署到 Vercel
- 后端和数据库部署到 Railway
- 最终给别人一个前端网址直接访问

## 一、先准备 GitHub 仓库

### 1. 创建仓库

在 GitHub 新建一个仓库，例如：

```text
ebay-monitor-mvp
```

### 2. 上传代码

把这个目录上传到 GitHub：

- `ebay_monitor_mvp`

### 3. 不要上传真实密钥

确认不要把真实 `.env` 上传到 GitHub。  
只保留：

- `.env.example`

## 二、Railway 部署数据库

### 1. 登录 Railway

打开：

- [https://railway.app](https://railway.app)

### 2. 新建项目

点击：

- `New Project`

### 3. 添加 PostgreSQL

点击：

- `Provision PostgreSQL`

创建完成后，Railway 会给你一个数据库服务。

### 4. 复制数据库连接串

进入 PostgreSQL 服务，找到：

- `Variables`

复制：

- `DATABASE_URL`

这个值后面填到后端服务环境变量里。

## 三、Railway 部署后端

### 1. 在同一个 Railway 项目里添加后端服务

点击：

- `New`
- `GitHub Repo`

选择你的 GitHub 仓库。

### 2. 设置后端根目录

进入后端服务设置，找到：

- `Root Directory`

填：

```text
backend
```

### 3. 设置启动命令

如果 Railway 没自动识别，手动填写：

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 4. 配置后端环境变量

进入：

- `Variables`

逐个新增：

```text
APP_ENV=production
DEBUG=false
API_PREFIX=/api
TIMEZONE=UTC
DATABASE_URL=Railway PostgreSQL 提供的连接串
EBAY_CLIENT_ID=你的 eBay Production Client ID
EBAY_CLIENT_SECRET=你的 eBay Production Client Secret
EBAY_MARKETPLACE_ID=EBAY_US
EBAY_API_BASE_URL=https://api.ebay.com
EBAY_AUTH_BASE_URL=https://api.ebay.com
EBAY_OAUTH_SCOPE=https://api.ebay.com/oauth/api_scope
EBAY_REQUEST_TIMEOUT_SECONDS=10
EBAY_MAX_RETRIES=3
ENABLE_SCHEDULER=false
CRON_SECRET=自己生成的一串强随机密钥
```

先不要急着填 `CORS_ALLOW_ORIGINS`，因为要等 Vercel 前端域名出来后再填。

### 5. 部署并验证后端

部署成功后，打开后端域名：

```text
https://你的-railway-后端域名/api/health
```

应该返回正常状态。

再打开：

```text
https://你的-railway-后端域名/docs
```

应该能看到 Swagger。

## 四、初始化线上数据库

### 方式 A：在 Railway shell 中执行

进入后端服务或数据库服务的 shell，执行建表脚本。

### 方式 B：本地连线上库执行

把本地环境变量临时切到线上 `DATABASE_URL`，然后运行：

```bash
cd backend
set PYTHONPATH=.
python scripts/init_db.py
```

如果需要导入样例数据，再执行：

```bash
psql "你的线上 DATABASE_URL" -f backend/scripts/seed_sample_data.sql
```

## 五、Vercel 部署前端

### 1. 登录 Vercel

打开：

- [https://vercel.com](https://vercel.com)

### 2. 导入 GitHub 仓库

点击：

- `Add New...`
- `Project`

选择同一个 GitHub 仓库。

### 3. 设置前端根目录

在导入配置页面找到：

- `Root Directory`

填：

```text
frontend
```

### 4. 配置前端环境变量

添加：

```text
VITE_API_BASE_URL=https://你的-railway-后端域名/api
```

### 5. 部署前端

部署完成后，你会得到一个前端网址，例如：

```text
https://xxx.vercel.app
```

## 六、回填后端 CORS

拿到前端网址后，回到 Railway 后端服务，补充环境变量：

```text
CORS_ALLOW_ORIGINS=https://xxx.vercel.app
```

如果你还有自定义域名，也可以写多个，用逗号分隔：

```text
https://xxx.vercel.app,https://your-domain.com
```

改完后重新部署后端。

## 七、配置 Railway Cron

### 1. 新建 Cron Job

在 Railway 项目中添加：

- `Cron`

### 2. 配置执行计划

建议每天一次，例如 UTC 09:00。

### 3. 配置调用命令

如果 Railway Cron 支持 curl 命令，使用：

```bash
curl -X POST "https://你的-railway-后端域名/api/ops/run-daily-crawl" -H "X-Cron-Secret: 你的CRON_SECRET"
```

### 4. 手动测试

先手动执行一次，确认后端返回：

- `requested`
- `succeeded`
- `failed`

## 八、上线后验收

按顺序检查：

1. 打开前端网址
2. 列表页是否能加载
3. 新增商品是否成功
4. 详情页是否正常
5. Excel 导出是否可用
6. CSV 导入是否可用
7. 手动调用 `/api/ops/run-daily-crawl` 是否成功

## 九、最终你发给别人的内容

只需要发：

- 前端网址，例如 `https://xxx.vercel.app`

不要发：

- Railway 后台
- PostgreSQL 连接串
- eBay `Client Secret`
- `.env`

## 十、建议的上线顺序

严格按下面顺序做，最不容易出错：

1. GitHub 上传代码
2. Railway 创建 PostgreSQL
3. Railway 部署后端
4. 初始化线上数据库
5. Vercel 部署前端
6. 回填后端 CORS
7. 配置 Railway Cron
8. 前后端联调验收
