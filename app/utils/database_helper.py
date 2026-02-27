from app import db
from sqlalchemy import create_engine, text
from contextlib import contextmanager

class DatabaseHelper:
    @staticmethod
    def get_connection_url(db_config):
        if db_config.db_type == 'sqlite':
            return f'sqlite:///{db_config.host}'
        elif db_config.db_type == 'mysql':
            return f'mysql+pymysql://{db_config.username}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}'
        elif db_config.db_type == 'postgresql':
            return f'postgresql://{db_config.username}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}'
        else:
            raise ValueError("Unsupported database type")

    @classmethod
    def execute_query(cls, db_config, query):
        url = cls.get_connection_url(db_config)
        engine = create_engine(url)
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query))
                if result.returns_rows:
                    columns = list(result.keys())
                    rows = [list(row) for row in result.fetchall()]
                    
                    return {
                        'status': 'success',
                        'columns': columns,
                        'rows': rows,
                        'count': len(rows)
                    }
                else:
                    conn.commit()
                    return {
                        'status': 'success',
                        'message': 'Query executed successfully (no rows returned)',
                        'count': 0
                    }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    @classmethod
    def test_connection(cls, db_config):
        """测试数据库连接是否成功"""
        url = cls.get_connection_url(db_config)
        engine = create_engine(url)
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return {'status': 'success', 'message': 'Connection successful'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
