"""
数据库管理模块
负责所有SQLite数据库操作，包括表创建、数据增删改查
"""
import sqlite3
import os
from datetime import datetime


class DatabaseManager:
    """数据库管理器，单例模式确保全局只有一个数据库连接"""
    
    _instance = None
    _connection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._connection is None:
            self.db_path = "word_game.db"
            self._create_connection()
            self._migrate_tables()
            self._create_tables()
    
    def _create_connection(self):
        """创建数据库连接"""
        self._connection = sqlite3.connect(self.db_path, check_same_thread=True)
        self._connection.row_factory = sqlite3.Row  # 支持字典式访问
        print("数据库连接已建立:", self.db_path)
    
    def _migrate_tables(self):
        """迁移数据库表结构"""
        cursor = self._connection.cursor()
        
        # 迁移words表（修改UNIQUE约束）
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='words'")
        words_sql = cursor.fetchone()
        if words_sql and 'UNIQUE(english, chinese)' in words_sql[0]:
            print("迁移words表结构...")
            cursor.execute("PRAGMA table_info(words)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # 创建临时表
            cursor.execute('''
                CREATE TABLE words_backup (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    english TEXT NOT NULL,
                    chinese TEXT NOT NULL,
                    source TEXT,
                    grade_level TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 复制数据（保留english唯一的第一条记录）
            cursor.execute('''
                INSERT INTO words_backup (english, chinese, source, grade_level, created_at)
                SELECT english, chinese, source, grade_level, created_at
                FROM words
                GROUP BY english
            ''')
            
            # 删除旧表
            cursor.execute("DROP TABLE words")
            
            # 重命名临时表
            cursor.execute("ALTER TABLE words_backup RENAME TO words")
            
            self._connection.commit()
            print("words表迁移完成")
        
        # 检查levels表是否需要迁移
        cursor.execute("PRAGMA table_info(levels)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 如果没有campaign_name字段，说明是旧表，需要迁移
        if 'campaign_name' in columns:
            # 检查是否有旧的UNIQUE约束（level_number单独UNIQUE）
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='levels'")
            create_sql = cursor.fetchone()
            if create_sql and 'level_number INTEGER NOT NULL UNIQUE' in create_sql[0]:
                # 需要迁移：备份旧数据，删除旧表，创建新表
                print("迁移levels表结构...")
                
                # 获取旧数据
                cursor.execute("SELECT * FROM levels")
                old_levels = cursor.fetchall()
                
                # 获取关卡单词关联数据
                cursor.execute("SELECT * FROM level_words")
                old_level_words = cursor.fetchall()
                
                # 删除旧表
                cursor.execute("DROP TABLE levels")
                cursor.execute("DROP TABLE level_words")
                
                # 创建新表（将在_create_tables中完成）
                self._connection.commit()
                print(f"levels表迁移完成，旧数据: {len(old_levels)}个关卡")
        
        cursor.close()
    
    def get_connection(self):
        """获取数据库连接"""
        return self._connection
    
    def _create_tables(self):
        """创建所有必要的表"""
        cursor = self._connection.cursor()
        
        # 单词表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english TEXT NOT NULL UNIQUE,
                chinese TEXT NOT NULL,
                source TEXT DEFAULT 'builtin',  -- builtin/custom
                grade_level TEXT,  -- 年级级别，如 "三年级上"
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 用户设置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # 每日打卡表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_checkin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,  -- YYYY-MM-DD
                new_words_count INTEGER DEFAULT 0,
                review_words_count INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                wrong_count INTEGER DEFAULT 0,
                accuracy REAL DEFAULT 0.0,
                duration_seconds INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 错词本表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wrong_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                english TEXT NOT NULL,
                chinese TEXT NOT NULL,
                error_count INTEGER DEFAULT 1,
                last_error_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                extra_practice_count INTEGER DEFAULT 0,  -- 还没记住的额外次数
                mastered INTEGER DEFAULT 0,  -- 是否彻底记住（1=是）
                FOREIGN KEY (word_id) REFERENCES words(id)
            )
        ''')
        
        # 关卡表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level_number INTEGER NOT NULL,
                campaign_name TEXT,
                grade_level TEXT,
                total_words INTEGER,
                status TEXT DEFAULT 'locked',  -- locked/active/completed
                best_accuracy REAL DEFAULT 0.0,
                best_score INTEGER DEFAULT 0,
                unlocked INTEGER DEFAULT 0,  -- 是否解锁
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(campaign_name, level_number)
            )
        ''')
        
        # 为已存在的levels表添加grade_level列（如果不存在）
        try:
            cursor.execute("ALTER TABLE levels ADD COLUMN grade_level TEXT")
        except sqlite3.OperationalError:
            pass  # 列已存在
        
        # 为已存在的levels表添加status列（如果不存在）
        try:
            cursor.execute("ALTER TABLE levels ADD COLUMN status TEXT DEFAULT 'locked'")
        except sqlite3.OperationalError:
            pass  # 列已存在
        
        # 为已存在的levels表添加daily_words列（如果不存在）
        try:
            cursor.execute("ALTER TABLE levels ADD COLUMN daily_words INTEGER")
        except sqlite3.OperationalError:
            pass  # 列已存在
        
        # 关卡单词关联表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS level_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level_id INTEGER NOT NULL,
                word_id INTEGER NOT NULL,
                FOREIGN KEY (level_id) REFERENCES levels(id),
                FOREIGN KEY (word_id) REFERENCES words(id)
            )
        ''')
        
        # 关卡尝试记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS level_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level_id INTEGER NOT NULL,
                attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_questions INTEGER,
                correct_count INTEGER,
                score INTEGER,
                accuracy REAL,
                duration_seconds INTEGER,
                FOREIGN KEY (level_id) REFERENCES levels(id)
            )
        ''')
        
        # 学习记录表（详细到每个单词的学习情况）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                learn_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_correct INTEGER,  -- 1=正确, 0=错误
                response_time_ms INTEGER,  -- 响应时间（毫秒）
                session_id TEXT,  -- 会话ID，用于分组
                FOREIGN KEY (word_id) REFERENCES words(id)
            )
        ''')
        
        # 学习场次表（每场学习的汇总数据）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_sessions (
                session_id TEXT PRIMARY KEY,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                total_questions INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                wrong_count INTEGER DEFAULT 0,
                accuracy REAL DEFAULT 0.0,
                duration_seconds INTEGER DEFAULT 0,
                grade_level TEXT,
                source TEXT  -- 'grade', 'custom', 'plan'
            )
        ''')
        
        self._connection.commit()
        print("数据库表创建完成")
    
    def execute(self, query, params=None):
        """执行SQL语句"""
        cursor = self._connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        self._connection.commit()
        return cursor
    
    def fetchone(self, query, params=None):
        """查询单条记录"""
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def fetchall(self, query, params=None):
        """查询多条记录"""
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            print("数据库连接已关闭")
    
    # ==================== 单词相关操作 ====================
    
    def add_word(self, english, chinese, source='custom', grade_level=None):
        """添加单词"""
        try:
            self.execute(
                "INSERT INTO words (english, chinese, source, grade_level) VALUES (?, ?, ?, ?)",
                (english, chinese, source, grade_level)
            )
            return True
        except sqlite3.IntegrityError:
            return False  # 单词已存在
    
    def add_words_batch(self, word_list, source='custom', grade_level=None):
        """批量添加单词"""
        cursor = self._connection.cursor()
        added_count = 0
        
        for english, chinese in word_list:
            try:
                # 先检查单词是否已存在
                cursor.execute(
                    "SELECT id, grade_level FROM words WHERE english = ?",
                    (english,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # 单词已存在，不修改grade_level（保持原有设置）
                    # 只更新chinese以确保释义最新
                    cursor.execute(
                        "UPDATE words SET chinese = ? WHERE english = ?",
                        (chinese, english)
                    )
                    # 不计入added_count，因为不是新单词
                else:
                    # 新单词，插入
                    cursor.execute(
                        "INSERT INTO words (english, chinese, source, grade_level) VALUES (?, ?, ?, ?)",
                        (english, chinese, source, grade_level)
                    )
                    added_count += 1
                    
            except Exception as e:
                print(f"添加单词失败: {english} - {e}")
        
        self._connection.commit()
        return added_count
    
    def get_words_by_grade(self, grade_level):
        """根据年级获取单词列表"""
        rows = self.fetchall(
            "SELECT id, english, chinese FROM words WHERE grade_level = ?",
            (grade_level,)
        )
        return [dict(row) for row in rows]
    
    def get_custom_words(self):
        """获取用户自定义单词"""
        rows = self.fetchall(
            "SELECT id, english, chinese FROM words WHERE source = 'custom'"
        )
        return [dict(row) for row in rows]
    
    def get_all_words(self):
        """获取所有单词"""
        rows = self.fetchall("SELECT id, english, chinese, grade_level FROM words")
        return [dict(row) for row in rows]
    
    def get_random_words(self, count, exclude_mastered=True):
        """随机获取指定数量的单词"""
        if exclude_mastered:
            rows = self.fetchall("""
                SELECT w.id, w.english, w.chinese 
                FROM words w
                LEFT JOIN wrong_words ww ON w.id = ww.word_id AND ww.mastered = 1
                WHERE ww.id IS NULL
                ORDER BY RANDOM()
                LIMIT ?
            """, (count,))
        else:
            rows = self.fetchall(
                "SELECT id, english, chinese FROM words ORDER BY RANDOM() LIMIT ?",
                (count,)
            )
        return [dict(row) for row in rows]
    
    # ==================== 设置相关操作 ====================
    
    def save_setting(self, key, value):
        """保存设置"""
        self.execute(
            "INSERT OR REPLACE INTO user_settings (key, value) VALUES (?, ?)",
            (key, str(value))
        )
    
    def get_setting(self, key, default=None):
        """获取设置"""
        row = self.fetchone(
            "SELECT value FROM user_settings WHERE key = ?",
            (key,)
        )
        return row['value'] if row else default
    
    # ==================== 错词本相关操作 ====================
    
    def add_wrong_word(self, word_id, english, chinese):
        """添加或更新错词"""
        # 检查是否已存在
        existing = self.fetchone(
            "SELECT id, error_count FROM wrong_words WHERE word_id = ?",
            (word_id,)
        )
        
        if existing:
            # 更新错误次数和时间
            self.execute(
                "UPDATE wrong_words SET error_count = error_count + 1, last_error_time = CURRENT_TIMESTAMP WHERE word_id = ?",
                (word_id,)
            )
        else:
            # 新增错词
            self.execute(
                "INSERT INTO wrong_words (word_id, english, chinese) VALUES (?, ?, ?)",
                (word_id, english, chinese)
            )
    
    def get_wrong_words(self, order_by_errors=True):
        """获取错词列表"""
        order = "ORDER BY error_count DESC" if order_by_errors else "ORDER BY last_error_time DESC"
        rows = self.fetchall(
            f"SELECT * FROM wrong_words WHERE mastered = 0 {order}"
        )
        return [dict(row) for row in rows]
    
    def mark_as_mastered(self, word_id):
        """标记为彻底记住"""
        self.execute(
            "UPDATE wrong_words SET mastered = 1 WHERE word_id = ?",
            (word_id,)
        )
    
    def add_extra_practice(self, word_id, count=3):
        """增加额外练习次数"""
        self.execute(
            "UPDATE wrong_words SET extra_practice_count = extra_practice_count + ? WHERE word_id = ?",
            (count, word_id)
        )
    
    def consume_extra_practice(self, word_id):
        """消耗一次额外练习次数"""
        self.execute(
            "UPDATE wrong_words SET extra_practice_count = MAX(0, extra_practice_count - 1) WHERE word_id = ?",
            (word_id,)
        )
    
    def get_extra_practice_count(self, word_id):
        """获取额外练习次数"""
        row = self.fetchone(
            "SELECT extra_practice_count FROM wrong_words WHERE word_id = ?",
            (word_id,)
        )
        return row['extra_practice_count'] if row else 0
    
    def clear_wrong_words(self):
        """清空错词本"""
        self.execute("DELETE FROM wrong_words")
    
    # ==================== 每日打卡相关操作 ====================
    
    def record_daily_checkin(self, date, new_words, review_words, correct, wrong, accuracy, duration):
        """记录每日学习打卡"""
        print(f"[DEBUG] record_daily_checkin called: date={date}, new_words={new_words}, correct={correct}, wrong={wrong}, accuracy={accuracy}, duration={duration}")
        self.execute("""
            INSERT OR REPLACE INTO daily_checkin 
            (date, new_words_count, review_words_count, correct_count, wrong_count, accuracy, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date, new_words, review_words, correct, wrong, accuracy, duration))
        print(f"[DEBUG] record_daily_checkin executed")
    
    def get_daily_checkin(self, date):
        """获取某天的打卡记录"""
        row = self.fetchone(
            "SELECT * FROM daily_checkin WHERE date = ?",
            (date,)
        )
        return dict(row) if row else None
    
    def get_monthly_checkins(self, year, month):
        """获取某月的所有打卡记录"""
        rows = self.fetchall(
            "SELECT * FROM daily_checkin WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?",
            (str(year), f"{month:02d}")
        )
        return [dict(row) for row in rows]
    
    def get_last_30_days_stats(self):
        """获取近30天的统计数据"""
        rows = self.fetchall("""
            SELECT date, accuracy, duration_seconds, correct_count, wrong_count
            FROM daily_checkin
            ORDER BY date DESC
            LIMIT 30
        """)
        return [dict(row) for row in rows]
    
    def get_session_stats(self):
        """获取所有学习场次的统计数据"""
        rows = self.fetchall("""
            SELECT session_id, accuracy, duration_seconds, correct_count, wrong_count,
                   (correct_count + wrong_count) as total_count, end_time
            FROM learning_sessions
            ORDER BY end_time DESC
            LIMIT 50
        """)
        result = [dict(row) for row in rows]
        print(f"[DEBUG] get_session_stats returned {len(result)} rows: {result}")
        return result
    
    def save_learning_session(self, session_id, total_questions, correct_count, wrong_count, duration_seconds, grade_level=None, source=None):
        """保存学习场次数据"""
        try:
            accuracy = (correct_count / total_questions * 100) if total_questions > 0 else 0
            print(f"[DEBUG] save_learning_session called: session_id={session_id}, total={total_questions}, correct={correct_count}, wrong={wrong_count}, duration={duration_seconds}")
            self.execute(
                """INSERT OR REPLACE INTO learning_sessions 
                   (session_id, total_questions, correct_count, wrong_count, accuracy, duration_seconds, grade_level, source, end_time)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (session_id, total_questions, correct_count, wrong_count, accuracy, duration_seconds, grade_level, source)
            )
            print(f"[DEBUG] save_learning_session executed")
            return True
        except Exception as e:
            print(f"保存学习场次失败: {e}")
            return False
    
    # ==================== 关卡相关操作 ====================
    
    def create_level(self, level_number, campaign_name, word_ids, grade_level=None, daily_words=None):
        """创建关卡"""
        cursor = self._connection.cursor()
        
        try:
            # 插入关卡
            cursor.execute(
                "INSERT INTO levels (level_number, campaign_name, grade_level, total_words, unlocked, daily_words) VALUES (?, ?, ?, ?, ?, ?)",
                (level_number, campaign_name, grade_level, len(word_ids), 1 if level_number == 1 else 0, daily_words)
            )
            level_id = cursor.lastrowid
            
            if level_id == 0:
                raise Exception("关卡插入失败，获取不到有效的level_id")
            
            # 关联单词
            for word_id in word_ids:
                cursor.execute(
                    "INSERT INTO level_words (level_id, word_id) VALUES (?, ?)",
                    (level_id, word_id)
                )
            
            self._connection.commit()
            return level_id
            
        except Exception as e:
            self._connection.rollback()
            print(f"创建关卡失败: {e}")
            return None
    
    def get_levels(self):
        """获取所有关卡"""
        rows = self.fetchall(
            "SELECT * FROM levels ORDER BY level_number"
        )
        return [dict(row) for row in rows]
    
    def get_level_words(self, level_id):
        """获取关卡的单词列表"""
        rows = self.fetchall("""
            SELECT w.id, w.english, w.chinese
            FROM level_words lw
            JOIN words w ON lw.word_id = w.id
            WHERE lw.level_id = ?
        """, (level_id,))
        return [dict(row) for row in rows]
    
    def update_level_status(self, level_id, accuracy, score):
        """更新关卡状态和最佳成绩"""
        # 获取当前最佳成绩
        current = self.fetchone(
            "SELECT best_accuracy, best_score FROM levels WHERE id = ?",
            (level_id,)
        )
        
        if current:
            best_acc = max(current['best_accuracy'], accuracy)
            best_score = max(current['best_score'], score)
            
            # 确定状态
            if accuracy >= 90:
                status = 'completed'
            else:
                status = 'active'
            
            self.execute("""
                UPDATE levels 
                SET best_accuracy = ?, best_score = ?, status = ?
                WHERE id = ?
            """, (best_acc, best_score, status, level_id))
            
            # 如果正确率>=90%，解锁下一关
            if accuracy >= 90:
                self.execute(
                    "UPDATE levels SET unlocked = 1 WHERE level_number = (SELECT level_number + 1 FROM levels WHERE id = ?)",
                    (level_id,)
                )
    
    def record_level_attempt(self, level_id, total, correct, score, accuracy, duration):
        """记录关卡尝试"""
        self.execute("""
            INSERT INTO level_attempts 
            (level_id, total_questions, correct_count, score, accuracy, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (level_id, total, correct, score, accuracy, duration))
    
    def get_level_attempts(self, level_id):
        """获取关卡的所有尝试记录"""
        rows = self.fetchall(
            "SELECT * FROM level_attempts WHERE level_id = ? ORDER BY attempt_date DESC",
            (level_id,)
        )
        return [dict(row) for row in rows]
    
    # ==================== 学习记录相关操作 ====================
    
    def record_learning(self, word_id, is_correct, response_time_ms, session_id):
        """记录学习详情"""
        self.execute("""
            INSERT INTO learning_records (word_id, is_correct, response_time_ms, session_id)
            VALUES (?, ?, ?, ?)
        """, (word_id, 1 if is_correct else 0, response_time_ms, session_id))
    
    def get_word_correct_count(self, word_id):
        """获取单词的正确次数"""
        row = self.fetchone(
            "SELECT COUNT(*) as count FROM learning_records WHERE word_id = ? AND is_correct = 1",
            (word_id,)
        )
        return row['count'] if row else 0
    
    def get_mastery_progress(self, word_ids):
        """获取一组单词的掌握进度"""
        result = {'mastered': 0, 'learning': 0, 'not_started': 0}
        
        for word_id in word_ids:
            correct_count = self.get_word_correct_count(word_id)
            wrong = self.fetchone(
                "SELECT id FROM wrong_words WHERE word_id = ?",
                (word_id,)
            )
            
            if correct_count >= 3:
                result['mastered'] += 1
            elif wrong:
                result['learning'] += 1
            else:
                result['not_started'] += 1
        
        return result
