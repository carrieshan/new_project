import logging
from app import db
from sqlalchemy import create_engine, text, inspect
from contextlib import contextmanager

logger = logging.getLogger('db_monitor')

# 引擎缓存，避免每次查询都创建新引擎
_engine_cache = {}

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
    def _get_engine(cls, db_config):
        """获取或创建引擎（带缓存）"""
        url = cls.get_connection_url(db_config)
        if url not in _engine_cache:
            _engine_cache[url] = create_engine(url, pool_pre_ping=True)
            logger.info(f"Created new engine for: {db_config.name}")
        return _engine_cache[url]

    @classmethod
    def dispose_engine(cls, db_config):
        """清理指定数据库的引擎缓存"""
        try:
            url = cls.get_connection_url(db_config)
            if url in _engine_cache:
                _engine_cache[url].dispose()
                del _engine_cache[url]
                logger.info(f"Disposed engine for: {db_config.name}")
        except Exception as e:
            logger.error(f"Failed to dispose engine: {e}")

    @classmethod
    def execute_query(cls, db_config, query):
        engine = cls._get_engine(db_config)
        
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
            logger.error(f"Query execution error: {e}")
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
        finally:
            engine.dispose()

    @classmethod
    def get_tables(cls, db_config):
        """获取数据库所有表名"""
        try:
            engine = cls._get_engine(db_config)
            inspector = inspect(engine)
            return {'status': 'success', 'tables': inspector.get_table_names()}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @classmethod
    def get_table_data(cls, db_config, table_name, limit=100, offset=0, filters=None):
        """获取表数据，支持分页和列筛选"""
        try:
            engine = cls._get_engine(db_config)
            
            # 验证表名是否存在，防止注入
            inspector = inspect(engine)
            if table_name not in inspector.get_table_names():
                return {'status': 'error', 'message': 'Table not found'}
            
            # 构建查询
            query_str = f"SELECT * FROM {table_name}"
            params = {}
            conditions = []
            
            columns_info = inspector.get_columns(table_name)
            col_names = [c['name'] for c in columns_info]
            
            # 列筛选
            if filters:
                for col, val in filters.items():
                    # 验证列名是否存在
                    if col in col_names and val is not None:
                        val_str = str(val).strip()
                        if val_str:
                            param_name = f"filter_{col}"
                            conditions.append(f"{col} LIKE :{param_name}")
                            params[param_name] = f"%{val_str}%"

            if conditions:
                query_str += " WHERE " + " AND ".join(conditions)

            # 获取总数 (用于分页)
            count_query = f"SELECT COUNT(*) FROM ({query_str}) as subquery"
            
            # 添加分页
            query_str += f" LIMIT {limit} OFFSET {offset}"
            
            with engine.connect() as conn:
                # 执行总数查询
                total_result = conn.execute(text(count_query), params)
                total = total_result.scalar()
                
                # 执行数据查询
                result = conn.execute(text(query_str), params)
                columns = list(result.keys())
                rows = [list(row) for row in result.fetchall()]
                
                return {
                    'status': 'success',
                    'columns': columns,
                    'rows': rows,
                    'total': total,
                    'limit': limit,
                    'offset': offset
                }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

