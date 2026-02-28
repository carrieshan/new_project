import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('db_monitor')

db = SQLAlchemy()
scheduler = APScheduler()

def create_app():
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///monitor.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    db.init_app(app)
    scheduler.init_app(app)
    scheduler.start()
    
    # 注册蓝图
    from app.views.main import main_bp
    from app.views.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 创建数据库表并加载任务
    with app.app_context():
        db.create_all()
        
        # 加载定时任务
        from app.models.database import ScheduledTask
        from app.utils.scheduler_helper import parse_cron
        
        try:
            tasks = ScheduledTask.query.all()
            for task in tasks:
                if task.is_active:
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
                        logger.info(f"Scheduled task {task.id}: {task.name}")
        except Exception as e:
            logger.error(f"Failed to load scheduled tasks: {e}")
        
    return app
