from flask import Blueprint, jsonify, request
from app import db
from app.models.database import DatabaseConfig, QueryHistory, ScheduledTask, SavedQuery
from app.utils.database_helper import DatabaseHelper
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
        'check_type': t.check_type
    } for t in tasks])

@api_bp.route('/tasks', methods=['POST'])
def add_task():
    data = request.json
    new_task = ScheduledTask(
        name=data['name'],
        db_config_id=data['db_config_id'],
        sql_query=data['query'],
        cron_expression=data['cron'],
        check_type=data.get('check_type', 'has_results'),
        threshold=data.get('threshold', 0)
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'status': 'success', 'id': new_task.id})

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
