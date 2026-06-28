"""
关卡系统模块
负责智能学习计划和关卡管理
"""
import math
from database import DatabaseManager


class LevelSystem:
    """关卡系统管理器"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_campaign(self, campaign_name, grade_level, days):
        """
        创建智能学习计划（战役）
        
        Args:
            campaign_name: 战役名称
            grade_level: 年级级别
            days: 计划完成天数
            
        Returns:
            dict: 包含关卡信息的字典
        """
        # 获取该年级的所有单词
        words = self.db.get_words_by_grade(grade_level)
        
        if not words:
            return None
        
        total_words = len(words)
        daily_words = math.ceil(total_words / days)
        
        print(f"创建战役: {campaign_name}")
        print(f"总单词数: {total_words}, 每天学习: {daily_words}个, 天数: {days}")
        
        # 按天拆分单词
        levels_data = []
        for i in range(0, total_words, daily_words):
            day_words = words[i:i+daily_words]
            level_number = len(levels_data) + 1
            levels_data.append({
                'level_number': level_number,
                'words': day_words
            })
        
        # 创建关卡
        created_levels = []
        for level_data in levels_data:
            word_ids = [w['id'] for w in level_data['words']]
            level_id = self.db.create_level(
                level_data['level_number'],
                campaign_name,
                word_ids,
                grade_level,  # 传递年级信息
                daily_words    # 传递每日单词数
            )
            
            if level_id is None:
                print(f"创建关卡 {level_data['level_number']} 失败")
                # 回滚：删除已创建的关卡
                for created in created_levels:
                    if created['level_id']:
                        self.db.execute("DELETE FROM level_words WHERE level_id = ?", (created['level_id'],))
                        self.db.execute("DELETE FROM levels WHERE id = ?", (created['level_id'],))
                return None
            
            created_levels.append({
                'level_id': level_id,
                'level_number': level_data['level_number'],
                'word_count': len(word_ids)
            })
        
        return {
            'campaign_name': campaign_name,
            'total_words': total_words,
            'daily_words': daily_words,
            'days': days,
            'levels': created_levels,
            'estimated_time_per_day': daily_words * 1.5  # 每个单词约1.5分钟
        }
    
    def get_all_levels(self):
        """获取所有关卡"""
        return self.db.get_levels()
    
    def get_level_detail(self, level_id):
        """
        获取关卡详细信息
        
        Args:
            level_id: 关卡ID
            
        Returns:
            dict: 关卡详情
        """
        levels = self.db.get_levels()
        level = next((l for l in levels if l['id'] == level_id), None)
        
        if not level:
            return None
        
        # 获取关卡单词
        words = self.db.get_level_words(level_id)
        
        # 获取尝试记录
        attempts = self.db.get_level_attempts(level_id)
        
        return {
            'level': level,
            'words': words,
            'attempts': attempts,
            'best_attempt': max(attempts, key=lambda x: x['accuracy']) if attempts else None
        }
    
    def is_level_unlocked(self, level_number):
        """
        检查关卡是否解锁
        
        Args:
            level_number: 关卡编号
            
        Returns:
            bool: 是否解锁
        """
        if level_number == 1:
            return True
        
        # 检查前一关的正确率
        prev_level = self.db.fetchone(
            "SELECT best_accuracy FROM levels WHERE level_number = ?",
            (level_number - 1,)
        )
        
        if prev_level and prev_level['best_accuracy'] >= 90:
            return True
        
        return False
    
    def unlock_next_level(self, current_level_id):
        """
        解锁下一关
        
        Args:
            current_level_id: 当前关卡ID
        """
        self.db.execute(
            "UPDATE levels SET unlocked = 1 WHERE level_number = (SELECT level_number + 1 FROM levels WHERE id = ?)",
            (current_level_id,)
        )
    
    def get_level_status_icon(self, level):
        """
        获取关卡状态图标
        
        Args:
            level: 关卡数据字典
            
        Returns:
            str: 状态图标和描述
        """
        if not level['unlocked']:
            return "🔒", "未解锁"
        
        accuracy = level['best_accuracy']
        
        if accuracy >= 100:
            return "👑", f"完美通关 ({accuracy:.0f}%)"
        elif accuracy >= 90:
            return "🟢", f"已通关 ({accuracy:.0f}%)"
        elif accuracy > 0:
            return "🟠", f"待提升 ({accuracy:.0f}%)"
        else:
            return "🔓", "可进入"
    
    def calculate_daily_plan(self, total_words, days):
        """
        计算每日学习计划
        
        Args:
            total_words: 总单词数
            days: 计划天数
            
        Returns:
            dict: 计划信息
        """
        daily_words = math.ceil(total_words / days)
        estimated_minutes = daily_words * 1.5
        
        return {
            'daily_words': daily_words,
            'estimated_minutes': estimated_minutes,
            'total_days': days
        }
    
    def get_all_campaigns(self):
        """
        获取所有学习计划（战役）
        
        Returns:
            list: 战役列表
        """
        # 获取所有不重复的战役名称
        campaigns_data = self.db.fetchall(
            "SELECT DISTINCT campaign_name, grade_level, created_at FROM levels ORDER BY created_at DESC"
        )
        
        campaigns = []
        for row in campaigns_data:
            campaign_name = row['campaign_name']
            # 获取该战役的所有关卡
            levels_raw = self.db.fetchall(
                "SELECT * FROM levels WHERE campaign_name = ? ORDER BY level_number",
                (campaign_name,)
            )
            # 转换sqlite3.Row为dict
            levels = [dict(l) for l in levels_raw]
            
            total_levels = len(levels)
            completed = len([l for l in levels if l.get('status') == 'completed'])
            
            # 获取daily_words（从第一个关卡获取）
            daily_words = levels[0].get('daily_words') if levels else 10
            
            campaigns.append({
                'campaign_name': campaign_name,
                'grade_level': row['grade_level'],
                'created_at': row['created_at'],
                'total_levels': total_levels,
                'completed_levels': completed,
                'daily_words': daily_words,
                'levels': levels
            })
        
        return campaigns
    
    def delete_campaign(self, campaign_name):
        """
        删除学习计划（战役）及其所有关卡
        
        Args:
            campaign_name: 战役名称
            
        Returns:
            bool: 是否成功
        """
        try:
            # 先删除关卡单词关联
            level_ids_raw = self.db.fetchall(
                "SELECT id FROM levels WHERE campaign_name = ?",
                (campaign_name,)
            )
            level_ids = [dict(l) for l in level_ids_raw]
            for level in level_ids:
                self.db.execute("DELETE FROM level_words WHERE level_id = ?", (level['id'],))
            
            # 删除关卡
            self.db.execute("DELETE FROM levels WHERE campaign_name = ?", (campaign_name,))
            
            return True
        except Exception as e:
            print(f"删除战役失败: {e}")
            return False
