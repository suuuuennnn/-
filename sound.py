"""
音效管理模块
支持 winsound 和 pygame 两种音效方案
"""
import winsound


class SoundManager:
    """音效管理器，提供游戏音效播放功能"""
    
    def __init__(self):
        self.sound_enabled = True
        # 音效配置：频率(Hz), 持续时间(ms)
        self.sound_configs = {
            "correct": (800, 150),   # 答对音效
            "wrong": (300, 300),     # 答错音效
            "combo": (1200, 200),    # 连击音效
            "game_over": (500, 500), # 游戏结束音效
            "click": (600, 50)       # 点击音效
        }
    
    def play_sound(self, sound_type):
        """播放指定类型的音效"""
        if not self.sound_enabled:
            return
        
        try:
            freq, duration = self.sound_configs.get(sound_type, (600, 200))
            winsound.Beep(freq, duration)
        except Exception as e:
            print(f"音效播放失败: {e}")
    
    def toggle_sound(self):
        """切换音效开关"""
        self.sound_enabled = not self.sound_enabled
        return self.sound_enabled
    
    def is_enabled(self):
        """检查音效是否开启"""
        return self.sound_enabled
