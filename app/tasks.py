from app import db
from app.models.database import ScheduledTask, DatabaseConfig, QueryHistory
from app.utils.database_helper import DatabaseHelper
import csv
import os
from datetime import datetime

def execute_task(task_id):
    """
    执行定时任务
    """
    # 确保在应用上下文中运行
    from app import scheduler
    with scheduler.app.app_context():
        task = ScheduledTask.query.get(task_id)
        if not task or not task.is_active:
            print(f"Task {task_id} not found or inactive")
            return

        print(f"Executing task: {task.name}")
        
        # 获取数据库配置
        db_config = DatabaseConfig.query.get(task.db_config_id)
        if not db_config:
            print(f"Database config {task.db_config_id} not found")
            return

        # 执行查询
        start_time = datetime.now()
        result = DatabaseHelper.execute_query(db_config, task.sql_query)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # 记录执行历史
        history = QueryHistory(
            db_config_id=task.db_config_id,
            sql_query=task.sql_query,
            status=result.get('status', 'error'),
            execution_time=execution_time,
            result_count=result.get('count', 0),
            error_message=result.get('error'),
            task_id=task.id
        )
        db.session.add(history)

        # 更新任务最后运行时间和状态
        task.last_run = end_time
        task.last_run_status = result.get('status', 'error')
        
        db.session.commit()

        # 保存结果为 CSV
        save_result_to_csv(task, result)

def save_result_to_csv(task, result):
    """
    保存查询结果为 CSV 文件
    """
    # 创建结果目录
    results_dir = os.path.join(os.getcwd(), 'results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    # 生成文件名: 任务名称_日期时间.csv
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{task.name}_{timestamp}.csv"
    filepath = os.path.join(results_dir, filename)

    try:
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            
            if result.get('status') == 'success' and 'columns' in result:
                # 写入表头
                writer.writerow(result['columns'])
                # 写入数据
                writer.writerows(result['rows'])
            else:
                # 如果查询失败或没有数据，写入空文件或错误信息
                # 用户要求"没有数据也生成空csv"，这里生成一个只有空内容的CSV，或者包含错误信息
                if result.get('status') == 'error':
                     writer.writerow(['Error', result.get('error')])
                else:
                     # 查询成功但无数据（例如非SELECT语句），或者空结果集
                     # 如果有列名，写入列名
                     if 'columns' in result:
                         writer.writerow(result['columns'])
                     else:
                         # 纯空文件
                         pass
        
        print(f"Result saved to {filepath}")
    except Exception as e:
        print(f"Failed to save CSV: {e}")
