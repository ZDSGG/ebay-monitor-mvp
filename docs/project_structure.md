# eBay 商品监控系统 MVP 项目结构

## Root
- `backend/`: FastAPI 后端
- `frontend/`: 前端工程占位，阶段 5 完成
- `sample_data/`: 示例 CSV 数据
- `docs/`: 项目结构与补充文档
- `.env.example`: 环境变量模板

## Backend
- `app/main.py`: FastAPI 入口
- `app/core/`: 配置、数据库、UTC 时间工具
- `app/models/`: SQLAlchemy ORM 模型
- `app/schemas/`: Pydantic 请求响应模型
- `app/services/`: 业务服务
- `scripts/init_db.py`: 数据库建表脚本
- `scripts/seed_sample_data.sql`: 示例数据脚本
