import json
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from app import db, scheduler
from app.models.database import DatabaseConfig, QueryHistory, ScheduledTask, SavedQuery, SystemConfig
from app.utils.database_helper import DatabaseHelper
from app.utils.scheduler_helper import parse_cron
from app.utils.email_helper import send_email
from app.utils.feishu_helper import send_feishu_message
from app.utils.dingtalk_helper import send_dingtalk_message
from app.utils.wechat_helper import send_wechat_message

logger = logging.getLogger('db_monitor')

api_bp = Blueprint('api', __name__)

@api_bp.route('/settings/smtp', methods=['GET'])
def get_smtp_config():
    keys = ['smtp_host', 'smtp_port', 'smtp_user', 'smtp_pass', 'smtp_from']
    config = {}
    for key in keys:
        item = SystemConfig.query.filter_by(key=key).first()
        config[key] = item.value if item else ''
    return jsonify(config)

@api_bp.route('/settings/smtp', methods=['POST'])
def save_smtp_config():
    data = request.json
    keys = ['smtp_host', 'smtp_port', 'smtp_user', 'smtp_pass', 'smtp_from']
    
    try:
        for key in keys:
            if key in data:
                item = SystemConfig.query.filter_by(key=key).first()
                if not item:
                    item = SystemConfig(key=key)
                    db.session.add(item)
                item.value = data[key]
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    task = ScheduledTask.query.get_or_404(id)
    data = request.json
    
    try:
        if 'name' in data: task.name = data['name']
        if 'db_config_id' in data: task.db_config_id = data['db_config_id']
        if 'sql_query' in data: task.sql_query = data['sql_query']
        if 'cron_expression' in data: task.cron_expression = data['cron_expression']
        if 'check_type' in data: task.check_type = data['check_type']
        if 'threshold' in data: task.threshold = data['threshold']
        if 'notify_email' in data: task.notify_email = data['notify_email']
        if 'notify_feishu' in data: task.notify_feishu = data['notify_feishu']
        if 'notify_dingtalk' in data: task.notify_dingtalk = data['notify_dingtalk']
        if 'notify_wechat' in data: task.notify_wechat = data['notify_wechat']
        if 'notify_rule' in data: task.notify_rule = data['notify_rule']
        
        db.session.commit()
        
        # Reschedule if active
        if task.is_active:
            try:
                scheduler.remove_job(str(task.id))
            except:
                pass
            
            from app.tasks import execute_task
            cron_args = parse_cron(task.cron_expression)
            if cron_args:
                scheduler.add_job(
                    func=execute_task,
                    trigger='cron',
                    args=[task.id],
                    id=str(task.id),
                    replace_existing=True,
                    **cron_args
                )
        
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    task = ScheduledTask.query.get_or_404(id)
    try:
        # Remove from scheduler
        try:
            scheduler.remove_job(str(task.id))
        except:
            pass
            
        # Delete history
        QueryHistory.query.filter_by(task_id=id).delete()
        
        db.session.delete(task)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/settings/feishu', methods=['GET'])
def get_feishu_config():
    keys = ['feishu_webhook', 'feishu_secret']
    config = {}
    for key in keys:
        item = SystemConfig.query.filter_by(key=key).first()
        config[key] = item.value if item else ''
    return jsonify(config)

@api_bp.route('/settings/feishu', methods=['POST'])
def save_feishu_config():
    data = request.json
    keys = ['feishu_webhook', 'feishu_secret']
    
    try:
        for key in keys:
            if key in data:
                item = SystemConfig.query.filter_by(key=key).first()
                if not item:
                    item = SystemConfig(key=key)
                    db.session.add(item)
                item.value = data[key]
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/settings/feishu/test', methods=['POST'])
def test_feishu_config():
    success = send_feishu_message("Test Message", "This is a test message from DB Monitor.")
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send Feishu message'}), 500

@api_bp.route('/settings/dingtalk', methods=['GET'])
def get_dingtalk_config():
    keys = ['dingtalk_webhook', 'dingtalk_secret']
    config = {}
    for key in keys:
        item = SystemConfig.query.filter_by(key=key).first()
        config[key] = item.value if item else ''
    return jsonify(config)

@api_bp.route('/settings/dingtalk', methods=['POST'])
def save_dingtalk_config():
    data = request.json
    keys = ['dingtalk_webhook', 'dingtalk_secret']
    
    try:
        for key in keys:
            if key in data:
                item = SystemConfig.query.filter_by(key=key).first()
                if not item:
                    item = SystemConfig(key=key)
                    db.session.add(item)
                item.value = data[key]
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/settings/dingtalk/test', methods=['POST'])
def test_dingtalk_config():
    success = send_dingtalk_message("Test Message", "This is a test message from DB Monitor.")
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send DingTalk message'}), 500

@api_bp.route('/settings/wechat', methods=['GET'])
def get_wechat_config():
    keys = ['wechat_webhook']
    config = {}
    for key in keys:
        item = SystemConfig.query.filter_by(key=key).first()
        config[key] = item.value if item else ''
    return jsonify(config)

@api_bp.route('/settings/wechat', methods=['POST'])
def save_wechat_config():
    data = request.json
    keys = ['wechat_webhook']
    
    try:
        for key in keys:
            if key in data:
                item = SystemConfig.query.filter_by(key=key).first()
                if not item:
                    item = SystemConfig(key=key)
                    db.session.add(item)
                item.value = data[key]
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/settings/wechat/test', methods=['POST'])
def test_wechat_config():
    success = send_wechat_message("Test Message", "This is a test message from DB Monitor.")
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send WeChat message'}), 500


@api_bp.route('/settings/smtp/test', methods=['POST'])
def test_smtp_config():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({'status': 'error', 'message': 'Email required'}), 400
    
    success = send_email(email, "Test Email", "This is a test email from DB Monitor.")
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send email'}), 500

@api_bp.route('/saved_queries', methods=['GET'])
def get_saved_queries():
    queries = SavedQuery.query.all()
    return jsonify([{
        'id': q.id,
        'name': q.name,
        'description': q.description,
        'sql_content': q.sql_content,
        'db_config_id': q.db_config_id
    } for q in queries])

@api_bp.route('/saved_queries', methods=['POST'])
def save_query():
    data = request.json
    new_query = SavedQuery(
        name=data['name'],
        description=data.get('description'),
        sql_content=data['sql_content'],
        db_config_id=data.get('db_config_id')
    )
    db.session.add(new_query)
    db.session.commit()
    return jsonify({'status': 'success', 'id': new_query.id})

@api_bp.route('/saved_queries/<int:id>', methods=['DELETE'])
def delete_saved_query(id):
    query = SavedQuery.query.get(id)
    if query:
        db.session.delete(query)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Not found'}), 404

@api_bp.route('/databases', methods=['GET'])
def get_databases():
    databases = DatabaseConfig.query.all()
    return jsonify([{
        'id': d.id,
        'name': d.name,
        'type': d.db_type,
        'host': d.host,
        'port': d.port,
        'database': d.database
    } for d in databases])

@api_bp.route('/databases/test', methods=['POST'])
def test_database():
    data = request.json
    try:
        # 创建临时配置对象进行测试，不保存到数据库
        temp_config = DatabaseConfig(
            name=data.get('name', 'temp_test'),
            db_type=data.get('db_type'),
            host=data.get('host'),
            port=int(data.get('port')) if data.get('port') else None,
            username=data.get('username'),
            password=data.get('password'),
            database=data.get('database')
        )
        result = DatabaseHelper.test_connection(temp_config)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@api_bp.route('/databases', methods=['POST'])
def add_database():
    data = request.json
    new_db = DatabaseConfig(
        name=data['name'],
        db_type=data['db_type'],
        host=data.get('host'),
        port=data.get('port'),
        username=data.get('username'),
        password=data.get('password'),
        database=data.get('database')
    )
    db.session.add(new_db)
    db.session.commit()
    return jsonify({'status': 'success', 'id': new_db.id})

@api_bp.route('/databases/<int:id>', methods=['PUT'])
def update_database(id):
    """编辑数据库配置"""
    db_config = DatabaseConfig.query.get_or_404(id)
    data = request.json
    try:
        if 'name' in data: db_config.name = data['name']
        if 'db_type' in data: db_config.db_type = data['db_type']
        if 'host' in data: db_config.host = data['host']
        if 'port' in data: db_config.port = data.get('port')
        if 'username' in data: db_config.username = data['username']
        if 'password' in data: db_config.password = data['password']
        if 'database' in data: db_config.database = data['database']
        
        # 清理旧引擎缓存
        DatabaseHelper.dispose_engine(db_config)
        
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/databases/<int:id>', methods=['DELETE'])
def delete_database(id):
    """删除数据库配置"""
    db_config = DatabaseConfig.query.get_or_404(id)
    try:
        # 检查是否有关联的定时任务
        tasks = ScheduledTask.query.filter_by(db_config_id=id).all()
        if tasks:
            return jsonify({
                'status': 'error',
                'message': f'该数据库下存在 {len(tasks)} 个关联任务，请先删除任务'
            }), 400
        
        # 清理引擎缓存
        DatabaseHelper.dispose_engine(db_config)
        
        # 删除关联的查询历史
        QueryHistory.query.filter_by(db_config_id=id).delete()
        
        db.session.delete(db_config)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    """首页仪表盘统计数据"""
    try:
        db_count = DatabaseConfig.query.count()
        task_count = ScheduledTask.query.count()
        active_task_count = ScheduledTask.query.filter_by(is_active=True).count()
        
        # 最近 10 条执行记录
        recent_history = QueryHistory.query.order_by(
            QueryHistory.created_at.desc()
        ).limit(10).all()
        
        success_count = sum(1 for h in recent_history if h.status == 'success')
        error_count = sum(1 for h in recent_history if h.status == 'error')
        
        return jsonify({
            'db_count': db_count,
            'task_count': task_count,
            'active_task_count': active_task_count,
            'recent_success': success_count,
            'recent_error': error_count
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/query/execute', methods=['POST'])
def execute_query():
    data = request.json
    db_id = data.get('db_id')
    query = data.get('query')
    
    db_config = DatabaseConfig.query.get(db_id)
    if not db_config:
        return jsonify({'status': 'error', 'message': 'Database not found'})
        
    result = DatabaseHelper.execute_query(db_config, query)
    
    # 记录历史
    history = QueryHistory(
        db_config_id=db_id,
        sql_query=query,
        status=result['status'],
        result_count=result.get('count', 0),
        error_message=result.get('error')
    )
    db.session.add(history)
    db.session.commit()
    
    return jsonify(result)

@api_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = ScheduledTask.query.all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'db_config_id': t.db_config_id,
        'sql_query': t.sql_query,
        'cron_expression': t.cron_expression,
        'check_type': t.check_type,
        'threshold': t.threshold,
        'is_active': t.is_active,
        'last_run': t.last_run.strftime('%Y-%m-%d %H:%M:%S') if t.last_run else None,
        'last_run_status': t.last_run_status,
        'notify_email': t.notify_email,
        'notify_feishu': t.notify_feishu,
        'notify_dingtalk': t.notify_dingtalk,
        'notify_wechat': t.notify_wechat,
        'notify_rule': t.notify_rule
    } for t in tasks])

@api_bp.route('/tasks/<int:id>/history', methods=['GET'])
def get_task_history(id):
    history = QueryHistory.query.filter_by(task_id=id).order_by(QueryHistory.created_at.desc()).limit(20).all()
    return jsonify([{
        'id': h.id,
        'status': h.status,
        'execution_time': h.execution_time,
        'result_count': h.result_count,
        'error_message': h.error_message,
        'created_at': h.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for h in history])

@api_bp.route('/tasks/<int:id>/toggle', methods=['POST'])
def toggle_task(id):
    task = ScheduledTask.query.get(id)
    if not task:
        return jsonify({'status': 'error', 'message': 'Task not found'}), 404
    
    try:
        task.is_active = not task.is_active
        db.session.commit()
        
        if task.is_active:
            # 启动任务
            cron_args = parse_cron(task.cron_expression)
            if cron_args:
                scheduler.add_job(
                    id=str(task.id),
                    func='app.tasks:execute_task',
                    args=[task.id],
                    trigger='cron',
                    replace_existing=True,
                    **cron_args
                )
        else:
            # 停止任务
            if scheduler.get_job(str(task.id)):
                scheduler.remove_job(str(task.id))
                
        return jsonify({'status': 'success', 'is_active': task.is_active})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/tasks', methods=['POST'])
def add_task():
    data = request.json
    try:
        new_task = ScheduledTask(
            name=data['name'],
            db_config_id=data['db_config_id'],
            sql_query=data.get('sql_query') or data.get('query'),
            cron_expression=data.get('cron_expression') or data.get('cron'),
            check_type=data.get('check_type', 'has_results'),
            threshold=data.get('threshold', 0),
            notify_email=data.get('notify_email'),
            notify_feishu=data.get('notify_feishu', False),
            notify_dingtalk=data.get('notify_dingtalk', False),
            notify_wechat=data.get('notify_wechat', False),
            notify_rule=data.get('notify_rule', 'none')
        )
        db.session.add(new_task)
        db.session.commit()
        
        # 添加到调度器
        cron_args = parse_cron(new_task.cron_expression)
        if cron_args:
            scheduler.add_job(
                id=str(new_task.id),
                func='app.tasks:execute_task',
                args=[new_task.id],
                trigger='cron',
                replace_existing=True,
                **cron_args
            )
            print(f"Added scheduled task {new_task.id}: {new_task.name}")
            
        return jsonify({'status': 'success', 'id': new_task.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400

@api_bp.route('/query/export_csv', methods=['POST'])
def export_csv():
    """
    将查询结果导出为 CSV 格式
    """
    from io import StringIO
    import csv
    from flask import Response
    
    data = request.json
    db_id = data.get('db_id')
    query = data.get('query')

    if not db_id or not query:
        return jsonify({'status': 'error', 'message': 'Missing db_id or query'}), 400

    db_config = DatabaseConfig.query.get(db_id)
    if not db_config:
        return jsonify({'status': 'error', 'message': 'Database not found'}), 404

    result = DatabaseHelper.execute_query(db_config, query)
    if result['status'] != 'success':
        return jsonify(result), 400
        
    if 'columns' not in result:
        return jsonify({'status': 'error', 'message': 'No data to export'}), 400

    # 创建 CSV 内容
    output = StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow(result['columns'])
    
    # 写入数据行
    for row in result['rows']:
        # 将 None 转换为 'NULL' 以匹配前端显示
        processed_row = []
        for cell in row:
            if cell is None:
                processed_row.append('NULL')
            else:
                processed_row.append(cell)
        writer.writerow(processed_row)

    # 获取 CSV 字符串
    csv_content = output.getvalue()
    output.close()

    # 返回 CSV 文件作为下载
    filename = f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@api_bp.route('/tasks/<int:id>/run', methods=['POST'])
def run_task(id):
    """
    手动触发执行定时任务
    """
    task = ScheduledTask.query.get(id)
    if not task:
        return jsonify({'status': 'error', 'message': 'Task not found'}), 404
    
    try:
        # 使用唯一ID添加到调度器立即执行
        job_id = f"manual_{id}_{datetime.now().timestamp()}"
        scheduler.add_job(
            id=job_id,
            func='app.tasks:execute_task',
            args=[id],
            trigger='date',
            run_date=datetime.now()
        )
        return jsonify({'status': 'success', 'message': '任务已触发执行'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/databases/<int:id>/tables', methods=['GET'])
def get_database_tables(id):
    db_config = DatabaseConfig.query.get(id)
    if not db_config:
        return jsonify({'status': 'error', 'message': 'Database not found'}), 404
    
    result = DatabaseHelper.get_tables(db_config)
    return jsonify(result)

@api_bp.route('/databases/<int:id>/tables/<table_name>/data', methods=['GET'])
def get_table_data(id, table_name):
    db_config = DatabaseConfig.query.get(id)
    if not db_config:
        return jsonify({'status': 'error', 'message': 'Database not found'}), 404
    
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # 获取 filters 参数 (JSON 字符串)
    filters_json = request.args.get('filters')
    column_filters = {}
    if filters_json:
        try:
            column_filters = json.loads(filters_json)
        except:
            pass
            
    result = DatabaseHelper.get_table_data(db_config, table_name, limit, offset, filters=column_filters)
    return jsonify(result)

@api_bp.route('/logs', methods=['GET'])
def get_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    task_id = request.args.get('task_id', type=int)
    status = request.args.get('status')
    
    # Select History, Task Name, DB Name
    query = db.session.query(QueryHistory, ScheduledTask.name.label('task_name'), DatabaseConfig.name.label('db_name'))\
        .outerjoin(ScheduledTask, QueryHistory.task_id == ScheduledTask.id)\
        .outerjoin(DatabaseConfig, QueryHistory.db_config_id == DatabaseConfig.id)
    
    if task_id:
        query = query.filter(QueryHistory.task_id == task_id)
    if status and status != 'all':
        query = query.filter(QueryHistory.status == status)
        
    pagination = query.order_by(QueryHistory.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    logs = []
    for item, task_name, db_name in pagination.items:
        logs.append({
            'id': item.id,
            'task_name': task_name or 'Manual Query',
            'db_name': db_name or 'Unknown',
            'sql_query': item.sql_query,
            'status': item.status,
            'execution_time': item.execution_time,
            'result_count': item.result_count,
            'error_message': item.error_message,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    return jsonify({
        'items': logs,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    })
