# views - 路由和 API

## 说明

使用 Flask Blueprint 组织的页面路由和 RESTful API 接口。

## 文件说明

| 文件 | 说明 |
|------|------|
| `main.py` | 页面路由蓝图 (`main_bp`)，渲染 6 个 HTML 页面 |
| `api.py` | API 蓝图 (`api_bp`)，约 25 个 RESTful 接口 |

## 页面路由 (main.py)

| 路由 | 页面 |
|------|------|
| `/` | 首页（仪表盘） |
| `/databases` | 数据库配置管理 |
| `/overview` | 数据库概览 |
| `/query` | SQL 查询 |
| `/tasks` | 定时任务管理 |
| `/logs` | 执行日志 |

## API 接口 (api.py)

| 分类 | 接口 |
|------|------|
| 数据库管理 | `GET/POST/PUT/DELETE /api/databases` |
| 数据库测试 | `POST /api/databases/test` |
| SQL 查询 | `POST /api/query/execute`, `GET/POST /api/queries` |
| 定时任务 | `GET/POST/PUT/DELETE /api/tasks`, `POST /api/tasks/<id>/run` |
| 系统设置 | `GET/POST /api/settings/{smtp,feishu,dingtalk,wechat}` |
| 仪表盘 | `GET /api/dashboard` |
| 数据浏览 | `GET /api/overview/*` |
| 导出 | `GET /api/query/export/csv` |
