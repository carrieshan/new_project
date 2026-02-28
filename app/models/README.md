# models - 数据模型

## 说明

使用 SQLAlchemy ORM 定义的数据库模型。

## 文件说明

| 文件 | 说明 |
|------|------|
| `database.py` | 所有数据模型定义 |

## 数据模型

| 模型 | 说明 | 主要字段 |
|------|------|---------|
| `DatabaseConfig` | 数据库连接配置 | name, db_type, host, port, username, password, database |
| `SavedQuery` | 保存的 SQL 查询 | name, description, sql_content, db_config_id |
| `QueryHistory` | 查询执行历史 | sql_query, status, execution_time, result_count, error_message |
| `SystemConfig` | 系统配置（键值对） | key, value, description |
| `ScheduledTask` | 定时任务 | name, cron_expression, check_type, threshold, notify_* |
