# new_project - 数据库监控系统

## 功能说明

基于 Flask 的数据库监控 Web 应用，支持多种数据库类型的连接管理、在线 SQL 查询、定时任务调度和多渠道告警通知。

## 核心功能

- **数据库管理** - 添加/编辑/删除数据库连接（SQLite、MySQL、PostgreSQL）
- **数据库概览** - 浏览数据库表结构和数据，支持分页和列筛选
- **SQL 查询** - 在线执行 SQL 查询，支持保存/加载常用 SQL、导出 CSV
- **定时任务** - Cron 调度 SQL 检查任务，支持异常阈值检测
- **多渠道通知** - 邮件(SMTP)、飞书、钉钉、企业微信 Webhook

## 技术栈

- **后端**: Flask, SQLAlchemy, Flask-APScheduler
- **前端**: Bootstrap 5, jQuery
- **数据库**: SQLite (内置), MySQL, PostgreSQL

## 启动方式

```bash
pip install -r requirements.txt
python run.py
```

访问 http://127.0.0.1:5000

## 目录结构

| 目录/文件 | 说明 |
|----------|------|
| `run.py` | 应用入口 |
| `requirements.txt` | 依赖清单 |
| `app/` | 应用主目录 |
| `results/` | CSV 导出结果目录 |
| `instance/` | SQLite 数据库文件（运行时生成） |