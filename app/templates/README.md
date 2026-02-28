# templates - HTML 模板

## 说明

Jinja2 模板文件，使用 Bootstrap 5 框架构建 UI，所有页面继承自 `base.html`。

## 文件说明

| 文件 | 说明 |
|------|------|
| `base.html` | 基础模板：导航栏、系统设置弹窗、Toast 通知组件、全局 JS 工具函数 |
| `index.html` | 首页：渐变色统计仪表盘（数据库数/任务数/成功率）+ 功能入口卡片 |
| `databases.html` | 数据库配置：列表展示、添加/编辑/删除数据库，测试连接 |
| `overview.html` | 数据库概览：树形展示数据库→表结构，表数据分页浏览和列筛选 |
| `query.html` | SQL 查询：在线编辑执行 SQL，保存/加载常用查询，结果表格展示，导出 CSV |
| `tasks.html` | 定时任务：任务 CRUD，Cron 调度配置，通知渠道选择，执行历史 |
| `logs.html` | 执行日志：查询历史记录列表 |

## 全局组件 (base.html)

- **Toast 通知** - `showToast(message, type)` 替代 `alert()`
- **配置保存** - `saveConfig()` 使用 `async/await + Promise.all`
- **Ajax 工具** - `postJson(url, data)` 返回 Promise
