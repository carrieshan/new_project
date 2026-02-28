# utils - 工具模块

## 说明

封装了数据库操作、消息通知和调度相关的工具函数。

## 文件说明

| 文件 | 说明 |
|------|------|
| `database_helper.py` | 数据库操作封装：连接管理（带引擎缓存）、SQL 执行、表数据查询、连接测试 |
| `scheduler_helper.py` | Cron 表达式解析：将 `分 时 日 月 周` 格式转为 APScheduler 参数 |
| `email_helper.py` | SMTP 邮件发送：支持 SSL/TLS，多收件人 |
| `feishu_helper.py` | 飞书 Webhook 通知：支持签名校验 |
| `dingtalk_helper.py` | 钉钉 Webhook 通知：支持 HMAC-SHA256 签名 |
| `wechat_helper.py` | 企业微信 Webhook 通知 |

## 引擎缓存机制 (database_helper.py)

`DatabaseHelper` 使用 `_engine_cache` 字典缓存已创建的 SQLAlchemy 引擎，避免每次查询都新建连接。当删除或编辑数据库配置时，通过 `dispose_engine()` 清理缓存。
