from flask import Blueprint, jsonify, request
from app import db, scheduler
from app.models.database import DatabaseConfig, QueryHistory, ScheduledTask, SavedQuery
from app.utils.database_helper import DatabaseHelper
from app.utils.scheduler_helper import parse_cron
import json
from datetime import datetime

api_bp = Blueprint('api', __name__)

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
    return jsonify([{'id': d.id, 'name': d.name, 'type': d.db_type} for d in databases])

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
        'cron_expression': t.cron_expression,
        'check_type': t.check_type,
        'is_active': t.is_active
    } for t in tasks])

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
            threshold=data.get('threshold', 0)
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
