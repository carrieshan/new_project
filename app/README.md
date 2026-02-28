# app - 应用主目录

## 说明

Flask 应用核心代码，采用蓝图（Blueprint）模式组织路由。

## 文件说明

| 文件 | 说明 |
|------|------|
| `__init__.py` | Flask 应用工厂，初始化数据库、调度器，注册蓝图，加载定时任务 |
| `tasks.py` | 定时任务执行逻辑，包含异常检测（check_type/threshold）和多渠道通知 |

## 子目录

| 目录 | 说明 |
|------|------|
| `models/` | ORM 数据模型定义 |
| `views/` | 路由和 API 接口 |
| `utils/` | 工具类（数据库操作、通知发送、Cron 解析） |
| `templates/` | Jinja2 HTML 模板 |
| `static/` | 静态资源（CSS/JS） |
| `config/` | 配置文件（预留） |
