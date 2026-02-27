# 如何运行数据库监控系统

1.  **安装依赖**:
    ```bash
    pip install Flask Flask-SQLAlchemy Flask-APScheduler SQLAlchemy pandas
    ```
    (如果您连接 MySQL 或 PostgreSQL，还需要安装 `pymysql` 或 `psycopg2-binary`)

2.  **启动应用**:
    ```bash
    python run.py
    ```

3.  **访问应用**:
    打开浏览器访问 `http://127.0.0.1:5000`

## 功能说明

-   **数据库管理**: 添加数据库连接信息。
-   **SQL查询**: 选择数据库并执行查询。
-   **定时任务**: 设置定时检查任务 (目前仅实现了添加和查看，调度逻辑已集成但需进一步完善执行细节)。
