import csv
import os
import logging
from datetime import datetime
from app import db
from app.models.database import ScheduledTask, DatabaseConfig, QueryHistory
from app.utils.database_helper import DatabaseHelper
from app.utils.email_helper import send_email
from app.utils.feishu_helper import send_feishu_message
from app.utils.dingtalk_helper import send_dingtalk_message
from app.utils.wechat_helper import send_wechat_message

logger = logging.getLogger('db_monitor')


def check_threshold(task, result):
    """
    根据 check_type 和 threshold 判断是否触发告警
    返回 (is_anomaly: bool, description: str)
    """
    count = result.get('count', 0)
    check_type = task.check_type or 'has_results'
    threshold = task.threshold or 0

    if check_type == 'has_results':
        if count > 0:
            return True, f"查询返回 {count} 条结果（预期：有结果时告警）"
        return False, f"查询无结果"
    elif check_type == 'no_results':
        if count == 0:
            return True, f"查询无结果（预期：无结果时告警）"
        return False, f"查询返回 {count} 条结果"
    elif check_type == 'count_gt':
        if count > threshold:
            return True, f"结果数 {count} > 阈值 {threshold}"
        return False, f"结果数 {count} <= 阈值 {threshold}"
    elif check_type == 'count_lt':
        if count < threshold:
            return True, f"结果数 {count} < 阈值 {threshold}"
        return False, f"结果数 {count} >= 阈值 {threshold}"
    
    return False, "未知检查类型"


def execute_task(task_id):
    """
    执行定时任务
    """
    # 确保在应用上下文中运行
    from app import scheduler
    with scheduler.app.app_context():
        task = ScheduledTask.query.get(task_id)
        if not task or not task.is_active:
            logger.warning(f"Task {task_id} not found or inactive")
            return

        logger.info(f"Executing task: {task.name}")
        
        # 获取数据库配置
        db_config = DatabaseConfig.query.get(task.db_config_id)
        if not db_config:
            logger.error(f"Database config {task.db_config_id} not found")
            return

        # 执行查询
        start_time = datetime.now()
        result = DatabaseHelper.execute_query(db_config, task.sql_query)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # 检查阈值条件
        is_anomaly = False
        anomaly_desc = ""
        status = result.get('status', 'error')
        
        if status == 'success':
            is_anomaly, anomaly_desc = check_threshold(task, result)
            logger.info(f"Task {task.name}: {anomaly_desc} (anomaly={is_anomaly})")

        # 记录执行历史
        history = QueryHistory(
            db_config_id=task.db_config_id,
            sql_query=task.sql_query,
            status=status,
            execution_time=execution_time,
            result_count=result.get('count', 0),
            error_message=result.get('error') or (anomaly_desc if is_anomaly else None),
            task_id=task.id
        )
        db.session.add(history)

        # 更新任务最后运行时间和状态
        task.last_run = end_time
        task.last_run_status = status
        
        db.session.commit()

        # 发送通知
        try:
            should_notify = False
            
            if task.notify_rule == 'both':
                should_notify = True
            elif task.notify_rule == 'failure' and (status == 'error' or is_anomaly):
                should_notify = True
            elif task.notify_rule == 'success' and status == 'success' and not is_anomaly:
                should_notify = True
                
            if should_notify:
                status_label = "异常" if is_anomaly else status.upper()
                subject = f"[{status_label}] 任务: {task.name}"
                body = f"""
                <h3>任务执行报告</h3>
                <p><b>任务名称:</b> {task.name}</p>
                <p><b>执行状态:</b> {status}</p>
                <p><b>检查结果:</b> {anomaly_desc}</p>
                <p><b>执行时间:</b> {end_time}</p>
                <p><b>结果数量:</b> {result.get('count', 0)}</p>
                <p><b>错误信息:</b> {result.get('error', '无')}</p>
                """
                text_msg = (
                    f"状态: {status}\n"
                    f"检查结果: {anomaly_desc}\n"
                    f"时间: {end_time}\n"
                    f"结果数: {result.get('count', 0)}\n"
                    f"错误: {result.get('error', '无')}"
                )
                
                if task.notify_email:
                    send_email(task.notify_email, subject, body)
                if task.notify_feishu:
                    send_feishu_message(subject, text_msg)
                if task.notify_dingtalk:
                    send_dingtalk_message(subject, text_msg)
                if task.notify_wechat:
                    send_wechat_message(subject, text_msg)
                    
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

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
                if result.get('status') == 'error':
                     writer.writerow(['Error', result.get('error')])
                else:
                     if 'columns' in result:
                         writer.writerow(result['columns'])
        
        logger.info(f"Result saved to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save CSV: {e}")

