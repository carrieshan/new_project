from app import db
from datetime import datetime

class DatabaseConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    db_type = db.Column(db.String(20), nullable=False)  # sqlite, mysql, postgresql
    host = db.Column(db.String(100))
    port = db.Column(db.Integer)
    username = db.Column(db.String(50))
    password = db.Column(db.String(100))
    database = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

class SavedQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sql_content = db.Column(db.Text, nullable=False)
    db_config_id = db.Column(db.Integer, db.ForeignKey('database_config.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class QueryHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    db_config_id = db.Column(db.Integer, db.ForeignKey('database_config.id'))
    sql_query = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20))  # success, error
    execution_time = db.Column(db.Float)  # seconds
    result_count = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    task_id = db.Column(db.Integer, db.ForeignKey('scheduled_task.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class ScheduledTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    db_config_id = db.Column(db.Integer, db.ForeignKey('database_config.id'))
    sql_query = db.Column(db.Text, nullable=False)
    cron_expression = db.Column(db.String(50), nullable=False)
    check_type = db.Column(db.String(20))  # has_results, no_results, count_gt, count_lt
    threshold = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime)
    last_run_status = db.Column(db.String(20))  # success, error
    created_at = db.Column(db.DateTime, default=datetime.now)
