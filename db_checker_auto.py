import sqlite3
import datetime
import os
from typing import List, Dict, Any
import json

class DatabaseChecker:
    """
    数据库检查器类，用于执行各种数据库健康检查
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.results = []
        
    def connect_db(self):
        """连接到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return None
    
    def check_table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        conn = self.connect_db()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            result = cursor.fetchone()
            exists = result is not None
            self.results.append({
                'check': f'表 {table_name} 是否存在',
                'result': '存在' if exists else '不存在',
                'status': '通过' if exists else '失败'
            })
            return exists
        except Exception as e:
            self.results.append({
                'check': f'表 {table_name} 是否存在',
                'result': f'错误: {str(e)}',
                'status': '错误'
            })
            return False
        finally:
            conn.close()
    
    def check_table_row_count(self, table_name: str) -> int:
        """检查表的行数"""
        conn = self.connect_db()
        if not conn:
            return -1
            
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            self.results.append({
                'check': f'{table_name} 表的行数',
                'result': f'{count} 行',
                'status': '通过'
            })
            return count
        except Exception as e:
            self.results.append({
                'check': f'{table_name} 表的行数',
                'result': f'错误: {str(e)}',
                'status': '错误'
            })
            return -1
        finally:
            conn.close()
    
    def check_column_info(self, table_name: str) -> List[tuple]:
        """检查表的列信息"""
        conn = self.connect_db()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            self.results.append({
                'check': f'{table_name} 表的列信息',
                'result': f'找到 {len(columns)} 列: {[col[1] for col in columns]}',
                'status': '通过'
            })
            return columns
        except Exception as e:
            self.results.append({
                'check': f'{table_name} 表的列信息',
                'result': f'错误: {str(e)}',
                'status': '错误'
            })
            return []
        finally:
            conn.close()
    
    def check_foreign_keys(self) -> List[tuple]:
        """检查外键约束"""
        conn = self.connect_db()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pragma_foreign_key_check;")
            fk_errors = cursor.fetchall()
            self.results.append({
                'check': '外键约束检查',
                'result': f'发现 {len(fk_errors)} 个外键问题' if fk_errors else '无外键问题',
                'status': '失败' if fk_errors else '通过'
            })
            return fk_errors
        except Exception as e:
            self.results.append({
                'check': '外键约束检查',
                'result': f'错误: {str(e)}',
                'status': '错误'
            })
            return []
        finally:
            conn.close()
    
    def check_database_integrity(self) -> bool:
        """检查数据库完整性"""
        conn = self.connect_db()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            is_ok = result[0] == 'ok'
            self.results.append({
                'check': '数据库完整性检查',
                'result': '完整' if is_ok else '损坏',
                'status': '通过' if is_ok else '失败'
            })
            return is_ok
        except Exception as e:
            self.results.append({
                'check': '数据库完整性检查',
                'result': f'错误: {str(e)}',
                'status': '错误'
            })
            return False
        finally:
            conn.close()
    
    def check_indexes(self) -> List[tuple]:
        """检查数据库索引"""
        conn = self.connect_db()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index';")
            indexes = cursor.fetchall()
            self.results.append({
                'check': '数据库索引检查',
                'result': f'找到 {len(indexes)} 个索引',
                'status': '通过'
            })
            return indexes
        except Exception as e:
            self.results.append({
                'check': '数据库索引检查',
                'result': f'错误: {str(e)}',
                'status': '错误'
            })
            return []
        finally:
            conn.close()
    
    def check_triggers(self) -> List[tuple]:
        """检查数据库触发器"""
        conn = self.connect_db()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger';")
            triggers = cursor.fetchall()
            self.results.append({
                'check': '数据库触发器检查',
                'result': f'找到 {len(triggers)} 个触发器',
                'status': '通过'
            })
            return triggers
        except Exception as e:
            self.results.append({
                'check': '数据库触发器检查',
                'result': f'错误: {str(e)}',
                'status': '错误'
            })
            return []
        finally:
            conn.close()
    
    def check_views(self) -> List[tuple]:
        """检查数据库视图"""
        conn = self.connect_db()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='view';")
            views = cursor.fetchall()
            self.results.append({
                'check': '数据库视图检查',
                'result': f'找到 {len(views)} 个视图',
                'status': '通过'
            })
            return views
        except Exception as e:
            self.results.append({
                'check': '数据库视图检查',
                'result': f'错误: {str(e)}',
                'status': '错误'
            })
            return []
        finally:
            conn.close()
    
    def run_all_checks(self, tables_to_check: List[str] = None):
        """运行所有检查"""
        print("开始数据库检查...")
        
        # 检查数据库完整性
        self.check_database_integrity()
        
        # 检查索引、触发器和视图
        self.check_indexes()
        self.check_triggers()
        self.check_views()
        
        # 如果没有指定要检查的表，则获取所有表名
        if tables_to_check is None:
            conn = self.connect_db()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables_to_check = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
                conn.close()
        
        # 对每个表执行检查
        for table_name in tables_to_check:
            self.check_table_exists(table_name)
            self.check_table_row_count(table_name)
            self.check_column_info(table_name)
        
        # 检查外键约束
        self.check_foreign_keys()
        
        print("数据库检查完成!")
    
    def generate_report(self, output_file: str = "database_check_report.txt"):
        """生成检查报告到txt文件"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"数据库检查报告\n")
            f.write(f"生成时间: {timestamp}\n")
            f.write("="*50 + "\n\n")
            
            # 统计信息
            total_checks = len(self.results)
            passed_checks = sum(1 for r in self.results if r['status'] == '通过')
            failed_checks = sum(1 for r in self.results if r['status'] == '失败')
            error_checks = sum(1 for r in self.results if r['status'] == '错误')
            
            f.write(f"总检查项: {total_checks}\n")
            f.write(f"通过: {passed_checks}\n")
            f.write(f"失败: {failed_checks}\n")
            f.write(f"错误: {error_checks}\n\n")
            
            # 详细结果
            f.write("详细检查结果:\n")
            f.write("-"*30 + "\n")
            for i, result in enumerate(self.results, 1):
                f.write(f"{i}. 检查项目: {result['check']}\n")
                f.write(f"   结果: {result['result']}\n")
                f.write(f"   状态: {result['status']}\n")
                f.write("\n")
        
        print(f"检查报告已生成: {output_file}")
        return output_file
    
    def generate_json_report(self, output_file: str = "database_check_report.json"):
        """生成JSON格式的检查报告"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report_data = {
            'report_title': '数据库检查报告',
            'generated_time': timestamp,
            'summary': {
                'total_checks': len(self.results),
                'passed_checks': sum(1 for r in self.results if r['status'] == '通过'),
                'failed_checks': sum(1 for r in self.results if r['status'] == '失败'),
                'error_checks': sum(1 for r in self.results if r['status'] == '错误')
            },
            'details': self.results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"JSON检查报告已生成: {output_file}")
        return output_file


def main():
    # 使用示例数据库
    sample_db = "sample_test.db"
    
    # 创建示例数据库用于测试
    conn = sqlite3.connect(sample_db)
    cursor = conn.cursor()
    
    # 创建一些示例表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);")
    
    # 插入一些示例数据
    cursor.execute("INSERT OR IGNORE INTO users (name, email) VALUES ('张三', 'zhangsan@example.com');")
    cursor.execute("INSERT OR IGNORE INTO users (name, email) VALUES ('李四', 'lisi@example.com');")
    cursor.execute("INSERT OR IGNORE INTO orders (user_id, product_name, quantity) VALUES (1, '笔记本电脑', 1);")
    cursor.execute("INSERT OR IGNORE INTO orders (user_id, product_name, quantity) VALUES (1, '鼠标', 2);")
    
    conn.commit()
    conn.close()
    
    print(f"使用示例数据库: {sample_db}")
    
    # 执行数据库检查
    checker = DatabaseChecker(sample_db)
    checker.run_all_checks(['users', 'orders'])  # 检查特定表
    checker.generate_report()
    checker.generate_json_report()


if __name__ == "__main__":
    main()