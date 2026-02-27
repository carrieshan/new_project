# 数据库监控系统 - 项目结构

## 项目目录结构

```
database_monitor/
├── app/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── database_config.py      # 数据库连接配置模块
│   │   └── mail_config.py          # 邮件服务配置
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py             # 数据库模型
│   │   ├── task.py                 # 任务模型
│   │   └── user.py                 # 用户模型
│   ├── views/
│   │   ├── __init__.py
│   │   ├── main.py                 # 主页面路由
│   │   ├── queries.py              # SQL查询页面路由
│   │   ├── tasks.py                # 任务管理页面路由
│   │   └── settings.py             # 设置页面路由
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── database_helper.py      # 数据库操作辅助函数
│   │   ├── scheduler.py            # 任务调度器
│   │   ├── mail_sender.py          # 邮件发送工具
│   │   └── validators.py           # 输入验证工具
│   └── static/
│       ├── css/
│       │   └── style.css
│       ├── js/
│       │   ├── main.js
│       │   └── query_editor.js
│       └── images/
├── migrations/                     # 数据库迁移文件
├── tests/                          # 测试文件
│   ├── __init__.py
│   ├── test_queries.py
│   ├── test_scheduler.py
│   └── test_mail.py
├── requirements.txt                # 依赖包列表
├── docker-compose.yml              # Docker配置
├── README.md                       # 项目说明
└── run.py                          # 应用启动文件
```

## 核心模块说明

### 1. 数据库连接配置模块 (config/database_config.py)
- 支持多种数据库类型的连接配置
- 加密存储敏感信息
- 连接测试功能

### 2. 数据库操作辅助函数 (utils/database_helper.py)
- 统一的数据库操作接口
- SQL执行安全检查
- 查询结果处理

### 3. 任务调度器 (utils/scheduler.py)
- 基于APScheduler的定时任务管理
- 任务持久化存储
- 执行状态监控

### 4. 邮件发送工具 (utils/mail_sender.py)
- SMTP配置管理
- 邮件模板系统
- 发送状态跟踪

## API 接口设计

### 数据库连接管理
- GET `/api/databases` - 获取所有数据库连接
- POST `/api/databases` - 添加新的数据库连接
- PUT `/api/databases/<id>` - 更新数据库连接
- DELETE `/api/databases/<id>` - 删除数据库连接
- POST `/api/databases/test` - 测试数据库连接

### SQL查询接口
- POST `/api/query` - 执行SQL查询
- POST `/api/query/validate` - 验证SQL语句

### 任务管理接口
- GET `/api/tasks` - 获取所有定时任务
- POST `/api/tasks` - 创建定时任务
- PUT `/api/tasks/<id>` - 更新定时任务
- DELETE `/api/tasks/<id>` - 删除定时任务

### 异常检测接口
- GET `/api/anomalies` - 获取异常检测结果
- POST `/api/anomalies/config` - 配置异常检测规则