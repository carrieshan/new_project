# new_project 项目分析报告

## 项目概述

这是一个基于 **Flask** 的 **数据库监控系统**，位于 `venv/demo/new_project/`。主要功能包括：

| 功能模块 | 说明 |
|---------|------|
| 数据库管理 | 添加/管理 SQLite、MySQL、PostgreSQL 连接 |
| 数据库概览 | 浏览数据库表结构和数据，支持分页和列筛选 |
| SQL 查询 | 在线执行 SQL、保存/加载常用 SQL、导出 CSV |
| 定时任务 | Cron 调度 SQL 检查任务，支持启停/手动执行/历史记录 |
| 多渠道通知 | 邮件(SMTP)、飞书、钉钉、企业微信 Webhook |

**技术栈**：Flask + SQLAlchemy + APScheduler + Bootstrap 5 + jQuery

---

## 发现的问题与改进建议

### 🔴 严重问题 (安全/Bug)

#### 1. SQL 注入风险
[database_helper.py](file:///c:/Users/lvmin/PycharmProjects/pythonProject1/venv/demo/new_project/app/utils/database_helper.py#L84) 中 `get_table_data` 使用 f-string 拼接表名：
```python
query_str = f"SELECT * FROM {table_name}"
```
虽然做了表名白名单验证（`inspector.get_table_names()`），但 `execute_query` 方法直接执行用户传入的任意 SQL，无任何权限限制——用户可执行 `DROP TABLE` 等破坏性操作。

**建议**：增加只读模式选项；对定时任务 SQL 限制只允许 SELECT。

#### 2. 密码明文存储
[database.py](file:///c:/Users/lvmin/PycharmProjects/pythonProject1/venv/demo/new_project/app/models/database.py#L11) 中 `DatabaseConfig.password` 和 `SystemConfig` 中的 SMTP 密码均为明文存储。

**建议**：使用 `cryptography.fernet` 对敏感字段加密存储。

#### 3. SECRET_KEY 硬编码
[__init__.py](file:///c:/Users/lvmin/PycharmProjects/pythonProject1/venv/demo/new_project/app/__init__.py#L12) 中 `app.config['SECRET_KEY'] = 'dev-secret-key'`。

**建议**：从环境变量或配置文件读取。

#### 4. 飞书签名 Bug
[feishu_helper.py](file:///c:/Users/lvmin/PycharmProjects/pythonProject1/venv/demo/new_project/app/utils/feishu_helper.py#L11) 中使用 `hmac.new()` 应为 `hmac.new` → 实际 Python 中是 `hmac.new`，但参数不对——飞书的签名算法要求先拼接 `timestamp + "\n" + secret`，再用 SHA256 HMAC，此处只传了一个参数作为 key，缺少 msg 参数。

**建议**：参考飞书官方文档修正签名逻辑。

---

### 🟡 功能缺陷

#### 5. 数据库配置无法编辑/删除
[databases.html](file:///c:/Users/lvmin/PycharmProjects/pythonProject1/venv/demo/new_project/app/templates/databases.html#L94-L95) 中"编辑"和"删除"按钮没有绑定任何事件，且后端也没有对应的 DELETE/PUT API。

#### 6. 数据库列表缺少 host 等详细信息
API `/api/databases` 只返回 `id`、`name`、`type`，[api.py L265](file:///c:/Users/lvmin/PycharmProjects/pythonProject1/venv/demo/new_project/app/views/api.py#L265) 未包含 `host`、`port`、`database` 等字段。

#### 7. 定时任务的 check_type/threshold 未实际使用
模型中有 `check_type` 和 `threshold` 字段，UI 也有对应表单，但 [tasks.py](file:///c:/Users/lvmin/PycharmProjects/pythonProject1/venv/demo/new_project/app/tasks.py) 中 `execute_task` 并没有根据这些字段做异常判断和告警。

#### 8. 引擎未复用导致连接泄漏
[database_helper.py](file:///c:/Users/lvmin/PycharmProjects/pythonProject1/venv/demo/new_project/app/utils/database_helper.py#L20) 每次查询都 `create_engine(url)`，未复用或 dispose 引擎，可能导致连接泄漏。

**建议**：使用引擎缓存或在 `execute_query` 后 `engine.dispose()`。

---

### 🟢 改进建议 (体验/架构)

#### 9. UI 较为基础
首页仅有三张简单卡片，无统计数据仪表盘。缺少：
- 数据库连接状态总览
- 最近任务执行成功/失败统计图表
- 系统运行状态监控

#### 10. 前端通知机制
所有操作结果都用 `alert()` 弹窗，体验较差。**建议**使用 Toast 通知。

#### 11. 缺少认证机制
系统无登录/权限控制，任何人可访问和操作。

#### 12. 缺少日志系统
全部使用 `print()` 输出，无持久化日志。**建议**使用 Python `logging` 模块。

#### 13. 配置保存回调地狱
[base.html](file:///c:/Users/lvmin/PycharmProjects/pythonProject1/venv/demo/new_project/app/templates/base.html#L186-L257) 中 `saveConfig` 使用了 4 层嵌套回调。**建议**改用 `Promise.all` 或 `async/await`。

#### 14. static 目录为空
CSS/JS 均使用 CDN，无本地静态资源。如需离线使用或优化加载速度可考虑本地化。

---

## 项目结构

```
new_project/
├── run.py                  # 应用入口
├── requirements.txt        # 依赖清单
├── app/
│   ├── __init__.py         # Flask 工厂 + 扩展初始化
│   ├── tasks.py            # 定时任务执行逻辑
│   ├── models/
│   │   └── database.py     # 5 个 ORM 模型
│   ├── views/
│   │   ├── main.py         # 页面路由 (5 个)
│   │   └── api.py          # REST API (约 20 个接口)
│   ├── utils/
│   │   ├── database_helper.py    # 数据库操作封装
│   │   ├── scheduler_helper.py   # Cron 表达式解析
│   │   ├── email_helper.py       # SMTP 邮件
│   │   ├── feishu_helper.py      # 飞书通知
│   │   ├── dingtalk_helper.py    # 钉钉通知
│   │   └── wechat_helper.py      # 企业微信通知
│   └── templates/                # Jinja2 模板 (6 个)
└── results/                      # CSV 输出目录
```
