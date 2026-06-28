"""
单词打地鼠游戏 - 主程序
整合所有模块，提供完整的游戏体验
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import os
import math
import random

# 导入自定义模块
from database import DatabaseManager
from sound import SoundManager
from image_utils import ImageUtils
from word_manager import WordManager
from levels import LevelSystem
from statistics import StatisticsGenerator
from calendar_view import CalendarView
from game import GameEngine


class WordWhackGame:
    """单词打地鼠游戏主类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🐭 专业版单词打地鼠")
        self.root.geometry("1000x850")
        self.root.configure(bg="#87CEEB")  # 天蓝色背景
        
        # 初始化管理器
        self.db = DatabaseManager()
        self.sound = SoundManager()
        self.images = ImageUtils()
        self.word_mgr = WordManager()
        self.level_sys = LevelSystem()
        
        # 清空自定义单词，让用户手动重新导入
        self.db.execute("DELETE FROM words WHERE source = 'custom'")
        print("已清空自定义单词，请手动导入 words.txt")
        
        # 加载图片
        self.images.load_all_images()
        
        # 自动导入年级词库
        count = self.word_mgr.scan_and_import_wordlists()
        print(f"已导入 {count} 个年级单词")
        
        # 游戏引擎
        self.game_engine = None
        
        # 当前设置
        self.current_grade = tk.StringVar(value="三年级上")
        self.daily_new_words = tk.IntVar(value=10)
        self.game_mode = tk.StringVar(value="eng2chn")
        self.words_per_round = tk.IntVar(value=20)
        
        # 单词来源选择: grade(年级词库) / custom(自定义) / plan(计划)
        self.word_source = tk.StringVar(value="grade")
        
        # 最新学习计划
        self.latest_plan = None
        
        # 创建主菜单
        self.create_main_menu()
    
    def create_main_menu(self):
        """创建主菜单界面"""
        self.clear_window()

        # 顶部框架（包含音效按钮和标题）
        top_frame = tk.Frame(self.root, bg="#87CEEB")
        top_frame.pack(fill=tk.X, pady=10)

        # 音效开关（左上角）
        tk.Button(top_frame,
                 text=f"🔊 音效: {'开' if self.sound.is_enabled() else '关'}",
                 font=("Microsoft YaHei", 12, "bold"),
                 bg="#FFB6C1",  # 浅粉色
                 fg="#FF1493",  # 深粉色
                 relief=tk.RAISED,
                 bd=3,
                 padx=15,
                 pady=5,
                 command=self.toggle_sound).pack(side=tk.LEFT, padx=10)

        # 标题（居中）
        title = tk.Label(top_frame, text="🐭 单词打地鼠游戏 🐭",
                        font=("Microsoft YaHei", 32, "bold"),
                        bg="#87CEEB", fg="#FFD700")
        title.pack(side=tk.LEFT, expand=True)

        # 单词来源选择
        source_frame = tk.Frame(self.root, bg="#87CEEB")
        source_frame.pack(pady=8, fill=tk.X, padx=20)
        
        tk.Label(source_frame, text="📚 单词来源：",
                font=("Microsoft YaHei", 14),
                bg="#87CEEB",
                fg="#2E8B57").pack(side=tk.LEFT, padx=10)
        
        # 年级词库选项
        grade_rb = tk.Radiobutton(source_frame, text="📖 年级词库",
                      variable=self.word_source, value="grade",
                      font=("Microsoft YaHei", 13),
                      bg="#87CEEB",
                      command=self.on_source_changed)
        grade_rb.pack(side=tk.LEFT, padx=8)
        
        # 自定义单词选项
        custom_rb = tk.Radiobutton(source_frame, text="📝 自定义单词",
                      variable=self.word_source, value="custom",
                      font=("Microsoft YaHei", 13),
                      bg="#87CEEB",
                      command=self.on_source_changed)
        custom_rb.pack(side=tk.LEFT, padx=8)
        
        # 智能计划选项
        self.plan_rb = tk.Radiobutton(source_frame, text="📋 智能计划",
                      variable=self.word_source, value="plan",
                      font=("Microsoft YaHei", 13),
                      bg="#87CEEB",
                      command=self.on_source_changed)
        self.plan_rb.pack(side=tk.LEFT, padx=8)
        
        # 单词来源选项面板（动态显示/隐藏）
        self.source_options_frame = tk.Frame(self.root, bg="#E0F7FA")
        self.source_options_frame.pack(pady=5, fill=tk.X, padx=40)
        
        # 年级选项面板
        self.grade_panel = tk.Frame(self.source_options_frame, bg="#E0F7FA")
        
        # 年级选择
        grade_label = tk.Label(self.grade_panel, text="选择年级：",
                font=("Microsoft YaHei", 13),
                bg="#E0F7FA",
                fg="#00695C")
        grade_label.pack(side=tk.LEFT, padx=5)
        
        grades = self.word_mgr.get_all_grades()
        grade_combo = ttk.Combobox(self.grade_panel,
                                  textvariable=self.current_grade,
                                  values=grades,
                                  width=15,
                                  font=("Microsoft YaHei", 12))
        grade_combo.pack(side=tk.LEFT, padx=5)
        
        # 年级单词数标签
        self.grade_count_label = tk.Label(self.grade_panel, text="",
                                        font=("Microsoft YaHei", 12),
                                        bg="#E0F7FA",
                                        fg="#FF6347")
        self.grade_count_label.pack(side=tk.LEFT, padx=10)
        
        # 自定义选项面板
        self.custom_panel = tk.Frame(self.source_options_frame, bg="#E0F7FA")
        
        # 导入自定义单词按钮
        tk.Button(self.custom_panel,
                 text="📁 导入自定义单词本",
                 font=("Microsoft YaHei", 12),
                 bg="#4CAF50",
                 fg="white",
                 relief=tk.RAISED, bd=3,
                 padx=12, pady=5,
                 command=self.import_custom_words).pack(side=tk.LEFT, padx=10)
        
        # 自定义单词数标签
        self.custom_count_label = tk.Label(self.custom_panel, text="",
                                        font=("Microsoft YaHei", 12),
                                        bg="#E0F7FA",
                                        fg="#FF6347")
        self.custom_count_label.pack(side=tk.LEFT, padx=10)
        
        # 计划选项面板
        self.plan_panel = tk.Frame(self.source_options_frame, bg="#E0F7FA")
        
        # 计划状态标签
        self.plan_count_label = tk.Label(self.plan_panel, text="暂无计划",
                                        font=("Microsoft YaHei", 12),
                                        bg="#E0F7FA",
                                        fg="#666666")
        self.plan_count_label.pack(side=tk.LEFT, padx=10)
        
        # 创建计划按钮
        tk.Button(self.plan_panel,
                 text="➕ 创建学习计划",
                 font=("Microsoft YaHei", 12),
                 bg="#FF9800",
                 fg="white",
                 relief=tk.RAISED, bd=3,
                 padx=12, pady=5,
                 command=self.show_smart_plan).pack(side=tk.LEFT, padx=10)
        
        # 查看计划按钮
        tk.Button(self.plan_panel,
                 text="📋 我的计划",
                 font=("Microsoft YaHei", 12),
                 bg="#2196F3",
                 fg="white",
                 relief=tk.RAISED, bd=3,
                 padx=12, pady=5,
                 command=self.show_my_plans).pack(side=tk.LEFT, padx=10)
        
        # 初始隐藏所有面板
        self.grade_panel.pack_forget()
        self.custom_panel.pack_forget()
        self.plan_panel.pack_forget()
        
        # 初始化单词来源显示
        self.root.after(100, self.on_source_changed)

        # 学习设置
        settings_frame = tk.Frame(self.root, bg="#87CEEB")
        settings_frame.pack(pady=12)

        tk.Label(settings_frame, text="每日新单词数：",
                font=("Microsoft YaHei", 15),
                bg="#87CEEB",
                fg="#2E8B57").pack(side=tk.LEFT, padx=10)

        tk.Spinbox(settings_frame,
                  from_=5, to=50,
                  width=12,
                  font=("Microsoft YaHei", 13),
                  textvariable=self.daily_new_words).pack(side=tk.LEFT, padx=10)

        tk.Label(settings_frame, text="每轮地鼠数：",
                font=("Microsoft YaHei", 15),
                bg="#87CEEB",
                fg="#2E8B57").pack(side=tk.LEFT, padx=20)

        tk.Spinbox(settings_frame,
                  from_=10, to=50,
                  width=12,
                  font=("Microsoft YaHei", 13),
                  textvariable=self.words_per_round).pack(side=tk.LEFT, padx=10)

        # 游戏模式选择
        mode_frame = tk.Frame(self.root, bg="#87CEEB")
        mode_frame.pack(pady=12)
        tk.Label(mode_frame, text="游戏模式：",
                font=("Microsoft YaHei", 15),
                bg="#87CEEB",
                fg="#2E8B57").pack(side=tk.LEFT, padx=10)

        tk.Radiobutton(mode_frame, text="英→中",
                      variable=self.game_mode,
                      value="eng2chn",
                      font=("Microsoft YaHei", 13),
                      bg="#87CEEB").pack(side=tk.LEFT, padx=10)

        tk.Radiobutton(mode_frame, text="中→英",
                      variable=self.game_mode,
                      value="chn2eng",
                      font=("Microsoft YaHei", 13),
                      bg="#87CEEB").pack(side=tk.LEFT, padx=10)
        
        # 主要功能按钮（圆角可爱风格）
        btn_frame1 = tk.Frame(self.root, bg="#87CEEB")
        btn_frame1.pack(pady=18)

        # 开始学习按钮 - 绿色
        tk.Button(btn_frame1, text="🎮 开始学习",
                 font=("Microsoft YaHei", 15, "bold"), width=16,
                 bg="#90EE90", fg="#2E8B57",  # 浅绿色背景，深绿色文字
                 relief=tk.RAISED, bd=4,
                 padx=12, pady=9,
                 command=self.start_learning).pack(side=tk.LEFT, padx=12)

        # 关卡挑战按钮 - 蓝色
        tk.Button(btn_frame1, text="🏆 关卡挑战",
                 font=("Microsoft YaHei", 15, "bold"), width=16,
                 bg="#87CEFA", fg="#1E90FF",  # 浅蓝色背景，深蓝色文字
                 relief=tk.RAISED, bd=4,
                 padx=12, pady=9,
                 command=self.show_levels).pack(side=tk.LEFT, padx=12)

        btn_frame2 = tk.Frame(self.root, bg="#87CEEB")
        btn_frame2.pack(pady=18)

        # 复习错词按钮 - 橙色
        tk.Button(btn_frame2, text="🔄 复习错词",
                 font=("Microsoft YaHei", 15, "bold"), width=16,
                 bg="#FFDAB9", fg="#FF6347",  # 桃色背景，橙红色文字
                 relief=tk.RAISED, bd=4,
                 padx=12, pady=9,
                 command=self.review_wrong_words).pack(side=tk.LEFT, padx=12)

        # 查看错词本按钮 - 红色
        tk.Button(btn_frame2, text="❌ 查看错词本",
                 font=("Microsoft YaHei", 15, "bold"), width=16,
                 bg="#FFB6C1", fg="#DC143C",  # 浅红色背景，深红色文字
                 relief=tk.RAISED, bd=4,
                 padx=12, pady=9,
                 command=self.show_wrong_words).pack(side=tk.LEFT, padx=12)

        # 统计和日历（圆角可爱风格）
        btn_frame3 = tk.Frame(self.root, bg="#87CEEB")
        btn_frame3.pack(pady=18)

        # 学习日历按钮 - 紫色
        tk.Button(btn_frame3, text="📅 学习日历",
                 font=("Microsoft YaHei", 15, "bold"), width=16,
                 bg="#DDA0DD", fg="#8B008B",  # 梅红色背景，深洋红色文字
                 relief=tk.RAISED, bd=4,
                 padx=12, pady=9,
                 command=self.show_calendar).pack(side=tk.LEFT, padx=12)

        # 学习统计按钮 - 青色
        tk.Button(btn_frame3, text="📊 学习统计",
                 font=("Microsoft YaHei", 15, "bold"), width=16,
                 bg="#AFEEEE", fg="#008B8B",  # 粉蓝色背景，深青色文字
                 relief=tk.RAISED, bd=4,
                 padx=12, pady=9,
                 command=self.show_statistics).pack(side=tk.LEFT, padx=12)

        # 个性化按钮 - 紫罗兰色
        tk.Button(self.root, text="🖼️ 更换图片",
                 font=("Microsoft YaHei", 13, "bold"),
                 bg="#E6E6FA", fg="#4B0082",  # 淡紫色背景，靛蓝色文字
                 relief=tk.RAISED, bd=3,
                 padx=18, pady=7,
                 command=self.change_image).pack(pady=12)

        # 智能计划按钮 - 金黄色
        plan_frame = tk.Frame(self.root, bg="#87CEEB")
        plan_frame.pack(pady=8)
        tk.Button(plan_frame, text="📋 智能学习计划",
                 font=("Microsoft YaHei", 13, "bold"),
                 bg="#FFFACD", fg="#DAA520",  # 柠檬绸色背景，金麒麟色文字
                 relief=tk.RAISED, bd=3,
                 padx=15, pady=7,
                 command=self.show_smart_plan).pack(side=tk.LEFT, padx=10)
        tk.Button(plan_frame, text="📑 我的计划",
                 font=("Microsoft YaHei", 13, "bold"),
                 bg="#E0FFFF", fg="#008B8B",  # 淡青色背景，深青色文字
                 relief=tk.RAISED, bd=3,
                 padx=15, pady=7,
                 command=self.show_my_plans).pack(side=tk.LEFT, padx=10)
    
    def create_rounded_button(self, parent, text, command, bg_color="#4CAF50", fg="white", 
                             font_size=14, width=15, pady=5):
        """
        创建圆角可爱风格按钮
        
        Args:
            parent: 父容器
            text: 按钮文字
            command: 点击回调
            bg_color: 背景色
            fg: 文字颜色
            font_size: 字体大小
            width: 按钮宽度
            pady: 垂直间距
        """
        # 使用Frame模拟圆角效果
        btn_frame = tk.Frame(parent, bg=bg_color, relief=tk.RAISED, bd=3)
        btn_frame.pack(pady=pady)
        
        btn = tk.Button(btn_frame, text=text,
                       font=("Arial Rounded MT Bold" if "Arial Rounded MT Bold" in 
                            [f for f in __import__('tkinter.font', fromlist=['Font']).fonts()] 
                            else "Arial", font_size, "bold"),
                       bg=bg_color, fg=fg,
                       width=width,
                       command=command,
                       relief=tk.FLAT,
                       padx=10, pady=5)
        btn.pack()
        
        return btn_frame
    
    def on_source_changed(self):
        """单词来源改变时更新显示"""
        source = self.word_source.get()
        
        # 先隐藏所有面板
        self.grade_panel.pack_forget()
        self.custom_panel.pack_forget()
        self.plan_panel.pack_forget()
        
        if source == "grade":
            # 显示年级选项面板
            self.grade_panel.pack(fill=tk.X, padx=20, pady=5)
            
            grade = self.current_grade.get()
            words = self.word_mgr.get_words_for_grade(grade)
            if words:
                self.grade_count_label.config(text=f"已加载 {len(words)} 个单词", fg="#4CAF50")
            else:
                self.grade_count_label.config(text="请导入词库", fg="#FF6347")
        
        elif source == "custom":
            # 显示自定义选项面板
            self.custom_panel.pack(fill=tk.X, padx=20, pady=5)
            
            words = self.db.get_custom_words()
            if words:
                self.custom_count_label.config(text=f"已加载 {len(words)} 个单词", fg="#4CAF50")
            else:
                self.custom_count_label.config(text="未导入", fg="#FF6347")
        
        elif source == "plan":
            # 显示计划选项面板
            self.plan_panel.pack(fill=tk.X, padx=20, pady=5)
            
            if self.latest_plan:
                self.plan_count_label.config(text=f"当前计划：{self.latest_plan['name']}", fg="#4CAF50")
            else:
                self.plan_count_label.config(text="暂无计划", fg="#FF6347")
                # 如果没有计划，自动切换到年级
                self.word_source.set("grade")
                self.root.after(50, self.on_source_changed)
    
    def clear_window(self):
        """清空窗口"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def toggle_sound(self):
        """切换音效"""
        enabled = self.sound.toggle_sound()
        messagebox.showinfo("音效设置", f"音效已{'开' if enabled else '关'}")
        self.create_main_menu()
    
    def import_custom_words(self):
        """导入自定义单词"""
        filename = filedialog.askopenfilename(
            title="选择单词本",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            print(f"用户选择了文件: {filename}")
            try:
                count = self.word_mgr.import_custom_wordlist(filename)
                if count > 0:
                    messagebox.showinfo("成功", f"成功导入 {count} 个单词！")
                    # 刷新显示
                    self.on_source_changed()
                else:
                    messagebox.showerror("导入失败", 
                        "没有找到有效的单词。\n\n请确保文件格式正确：\n- 每行一个单词\n- 格式: 英文,中文\n- 示例: apple,苹果\n\n注意：如果所有单词已存在，也会显示为0个。")
            except Exception as e:
                messagebox.showerror("导入错误", f"导入过程中发生错误：\n{str(e)}")
    
    def start_learning(self):
        """开始学习 - 根据用户选择的单词来源"""
        source = self.word_source.get()
        today_words = []
        
        if source == "plan":
            # 使用智能计划
            if not self.latest_plan:
                messagebox.showwarning("警告", "请先创建智能学习计划！")
                return
            
            grade = self.latest_plan['grade']
            daily_words = self.latest_plan['daily_words']
            
            if grade == 'custom':
                words = self.db.get_custom_words()
            else:
                words = self.word_mgr.get_words_for_grade(grade)
            
            if not words:
                messagebox.showwarning("警告", f"计划中的单词来源（{grade}）没有单词！")
                return
            
            count = min(daily_words, len(words))
            today_words = random.sample(words, count)
            print(f"使用计划({self.latest_plan['name']}): {len(today_words)}个单词")
        
        elif source == "custom":
            # 使用自定义单词
            words = self.db.get_custom_words()
            
            if not words:
                messagebox.showwarning("警告", "没有自定义单词！\n\n请先导入自定义单词本")
                return
            
            daily_count = self.daily_new_words.get()
            count = min(daily_count, len(words))
            today_words = random.sample(words, count)
            print(f"使用自定义单词: {len(today_words)}个")
        
        else:  # source == "grade"
            # 使用年级词库
            grade = self.current_grade.get()
            words = self.word_mgr.get_words_for_grade(grade)
            
            if not words or len(words) == 0:
                messagebox.showwarning("警告", f"{grade} 没有单词！\n\n请先在wordlists文件夹添加词库文件")
                return
            
            daily_count = self.daily_new_words.get()
            count = min(daily_count, len(words))
            today_words = random.sample(words, count)
            print(f"使用年级单词({grade}): {len(today_words)}个")
        
        if not today_words or len(today_words) == 0:
            messagebox.showwarning("警告", "没有足够的可用单词！")
            return
        
        print(f"准备显示预览窗口，单词数: {len(today_words)}")
        # 显示预览窗口
        self.show_preview_window(today_words, lambda: self.start_game_session(today_words))
    
    def show_preview_window(self, words, start_callback):
        """
        显示单词预览窗口
        
        Args:
            words: 单词列表
            start_callback: 开始游戏的回调函数
        """
        print(f"显示预览窗口，单词数: {len(words)}")
        
        preview_win = tk.Toplevel(self.root)
        preview_win.title("📖 单词预览")
        preview_win.geometry("600x500")
        preview_win.configure(bg="#FFF9C4")  # 淡黄色背景
        
        tk.Label(preview_win, text="📖 本轮单词预览", 
                font=("Arial", 20, "bold"),
                bg="#FFF9C4", fg="#F57F17").pack(pady=10)
        
        tk.Label(preview_win, text=f"共 {len(words)} 个单词，请快速记忆！",
                font=("Arial", 12),
                bg="#FFF9C4", fg="#F57F17").pack(pady=5)
        
        # 单词列表
        list_frame = tk.Frame(preview_win, bg="#FFF9C4")
        list_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        canvas = tk.Canvas(list_frame, bg="#FFF9C4")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#FFF9C4")
        
        scroll_frame.bind("<Configure>", 
                         lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for i, word in enumerate(words):
            meanings = self.word_mgr.parse_word_meanings(word['chinese'])
            meaning_text = "; ".join(meanings[:2])  # 只显示前两个释义
            
            tk.Label(scroll_frame, 
                    text=f"{i+1}. {word['english']} - {meaning_text}",
                    font=("Arial", 12),
                    bg="#FFF9C4", fg="#2E8B57",
                    anchor="w").pack(fill=tk.X, padx=5, pady=2)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 倒计时
        countdown_label = tk.Label(preview_win, text="", 
                                  font=("Arial", 16, "bold"),
                                  bg="#FFF9C4", fg="#F44336")
        countdown_label.pack(pady=5)
        
        # 提前开始按钮（圆角可爱风格）
        def start_game():
            print("点击提前开始按钮")
            if preview_win.winfo_exists():
                preview_win.destroy()
            print("调用 start_callback")
            try:
                start_callback()
                print("start_callback 执行成功")
            except Exception as e:
                print(f"start_callback 执行失败: {e}")
                import traceback
                traceback.print_exc()
        
        tk.Button(preview_win, text="▶ 提前开始", 
                 font=("Arial", 14, "bold"), 
                 bg="#90EE90", fg="#2E8B57",
                 relief=tk.RAISED,
                 bd=3,
                 padx=15,
                 pady=5,
                 command=start_game).pack(pady=10)
        
        # 倒计时逻辑
        remaining = [30]  # 使用列表以便在闭包中修改
        
        def update_countdown():
            if remaining[0] > 0 and preview_win.winfo_exists():
                countdown_label.config(text=f"⏱ {remaining[0]} 秒后自动开始")
                remaining[0] -= 1
                preview_win.after(1000, update_countdown)
            elif preview_win.winfo_exists():
                # 倒计时结束，先销毁窗口再开始游戏
                print("倒计时结束，准备开始游戏")
                preview_win.destroy()
                try:
                    start_callback()
                    print("倒计时结束后 start_callback 执行成功")
                except Exception as e:
                    print(f"倒计时结束后 start_callback 执行失败: {e}")
                    import traceback
                    traceback.print_exc()
        
        print("启动倒计时")
        update_countdown()
    
    def start_game_session(self, words, is_next_round=False):
        """开始游戏会话"""
        print(f"[DEBUG] start_game_session called with {len(words) if words else 0} words, is_next_round={is_next_round}")
        # 保存当前单词列表，用于再来一次
        self._current_words = words
        
        mode = self.game_mode.get()
        total = self.words_per_round.get()
        
        def on_game_over(result):
            print(f"[DEBUG] on_game_over called with result: {result}")
            if result:
                # 记录每日打卡
                today = datetime.now().strftime("%Y-%m-%d")
                new_words = len(set(w['id'] for w in words))
                
                self.db.record_daily_checkin(
                    today,
                    new_words,
                    0,  # 复习单词数（简化）
                    result['correct'],
                    result['wrong'],
                    result['accuracy'],
                    result['duration']
                )
                
                # 记录学习场次
                import uuid
                session_id = str(uuid.uuid4())[:8]
                source = self.word_source.get()
                grade = self.current_grade.get() if source == "grade" else None
                self.db.save_learning_session(
                    session_id,
                    result['correct'] + result['wrong'],
                    result['correct'],
                    result['wrong'],
                    result['duration'],
                    grade,
                    source
                )
            
            # 返回主菜单
            self.create_main_menu()
        
        def restart_callback():
            """再来一次 - 使用相同的单词"""
            # 重新开始，使用保存的单词
            self.start_game_session(self._current_words, is_next_round=False)
        
        def next_round_callback(result):
            """下一轮 - 获取新单词重新开始"""
            print(f"[DEBUG] next_round_callback called with result: {result}")
            # 获取新单词
            new_words = self._get_new_words()
            print(f"[DEBUG] _get_new_words returned {len(new_words) if new_words else 0} words")
            if new_words:
                self.start_game_session(new_words, is_next_round=True)
            else:
                print("[DEBUG] No new words available, showing message")
                messagebox.showinfo("提示", "没有更多单词了！")
                self.create_main_menu()
        
        # 创建游戏引擎
        self.game_engine = GameEngine(self.root, self.db, self.sound, self.images)
        self.game_engine.start_game(words, mode, total, on_game_over, restart_callback, next_round_callback)
    
    def _get_new_words(self):
        """获取新单词（用于再来一局）- 排除当前已学过的单词"""
        source = self.word_source.get()
        
        if source == "grade":
            grade = self.current_grade.get()
            words = self.word_mgr.get_words_for_grade(grade)
        elif source == "custom":
            words = self.db.get_custom_words()
        elif source == "plan" and self.latest_plan:
            # 从计划中获取单词
            words = []
            for level in self.latest_plan.get('levels', []):
                # 兼容 level_id 或 id
                level_id = level.get('level_id', level.get('id'))
                if level_id:
                    level_words = self.db.get_level_words(level_id)
                    words.extend(level_words)
        else:
            words = []
        
        if not words:
            return []
        
        # 获取当前已学过的单词ID
        current_word_ids = set(w['id'] for w in self._current_words) if hasattr(self, '_current_words') else set()
        
        # 过滤掉已学过的单词
        new_words = [w for w in words if w['id'] not in current_word_ids]
        
        if not new_words:
            # 如果没有新单词了，返回所有单词（允许重复学习）
            new_words = words
        
        # 随机打乱顺序
        import random
        random.shuffle(new_words)
        
        # 返回指定数量的单词
        total = self.words_per_round.get()
        return new_words[:min(total * 2, len(new_words))]
    
    def review_wrong_words(self):
        """复习错词"""
        wrong_words_data = self.db.get_wrong_words()
        
        if not wrong_words_data:
            messagebox.showinfo("提示", "错词本为空，无需复习")
            return
        
        # 提取单词数据
        review_words = []
        for ww in wrong_words_data[:20]:  # 最多20个
            review_words.append({
                'id': ww['word_id'],
                'english': ww['english'],
                'chinese': ww['chinese']
            })
        
        if not review_words:
            messagebox.showinfo("提示", "没有可复习的错词")
            return
        
        self.show_preview_window(review_words, 
                                lambda: self.start_game_session(review_words))
    
    def show_wrong_words(self):
        """显示错词本"""
        dialog = tk.Toplevel(self.root)
        dialog.title("❌ 错词本")
        dialog.geometry("800x600")
        dialog.configure(bg="#87CEEB")
        
        tk.Label(dialog, text="❌ 错词本", 
                font=("Arial", 24, "bold"),
                bg="#87CEEB", fg="#F44336").pack(pady=10)
        
        wrong_list = self.db.get_wrong_words()
        tk.Label(dialog, text=f"共有 {len(wrong_list)} 个错词",
                font=("Arial", 14),
                bg="#87CEEB", fg="#2E8B57").pack(pady=5)
        
        # 滚动列表
        canvas = tk.Canvas(dialog, bg="#87CEEB")
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#87CEEB")
        
        scroll_frame.bind("<Configure>", 
                         lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        if wrong_list:
            for idx, ww in enumerate(wrong_list):
                frame = tk.Frame(scroll_frame, bg="#E3F2FD", relief=tk.RAISED, bd=2)
                frame.pack(fill=tk.X, padx=10, pady=5)
                
                tk.Label(frame, 
                        text=f"{idx+1}. {ww['english']} - 错误次数: {ww['error_count']}",
                        font=("Arial", 14, "bold"),
                        bg="#E3F2FD", fg="#F44336",
                        anchor="w").pack(fill=tk.X, padx=10, pady=5)
                
                meanings = "; ".join(self.word_mgr.parse_word_meanings(ww['chinese']))
                tk.Label(frame, text=f"释义: {meanings}",
                        font=("Arial", 12),
                        bg="#E3F2FD", fg="#2E8B57",
                        anchor="w", wraplength=700).pack(fill=tk.X, padx=10, pady=2)
                
                tk.Label(frame, 
                        text=f"最后错误: {ww['last_error_time']}",
                        font=("Arial", 10),
                        bg="#E3F2FD", fg="#666",
                        anchor="w").pack(fill=tk.X, padx=10, pady=2)
                
                # 操作按钮
                btn_frame = tk.Frame(frame, bg="#E3F2FD")
                btn_frame.pack(fill=tk.X, padx=10, pady=5)
                
                tk.Button(btn_frame, text="还没记住 (+3次)",
                         font=("Arial", 10, "bold"),
                         bg="#FFDAB9", fg="#FF6347",
                         relief=tk.RAISED,
                         bd=2,
                         padx=8,
                         pady=3,
                         command=lambda wid=ww['word_id']: self.add_extra_practice(wid, dialog)).pack(side=tk.LEFT, padx=5)
                
                tk.Button(btn_frame, text="彻底记住",
                         font=("Arial", 10, "bold"),
                         bg="#90EE90", fg="#2E8B57",
                         relief=tk.RAISED,
                         bd=2,
                         padx=8,
                         pady=3,
                         command=lambda wid=ww['word_id']: self.mark_mastered(wid, dialog)).pack(side=tk.LEFT, padx=5)
        else:
            tk.Label(scroll_frame, text="暂无错词，继续加油！",
                    font=("Arial", 16),
                    bg="#87CEEB", fg="#2E8B57").pack(pady=50)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        btn_frame = tk.Frame(dialog, bg="#87CEEB")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="🗑️ 清空错词本",
                 font=("Arial", 12, "bold"),
                 bg="#FFB6C1", fg="#DC143C",
                 relief=tk.RAISED,
                 bd=3,
                 padx=10,
                 pady=5,
                 command=lambda: self.clear_wrong_words(dialog)).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="关闭",
                 font=("Arial", 12, "bold"),
                 bg="#AFEEEE", fg="#008B8B",
                 relief=tk.RAISED,
                 bd=3,
                 padx=10,
                 pady=5,
                 command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def add_extra_practice(self, word_id, dialog):
        """添加额外练习"""
        self.db.add_extra_practice(word_id, 3)
        messagebox.showinfo("成功", "已添加3次额外练习")
        dialog.destroy()
        self.show_wrong_words()
    
    def mark_mastered(self, word_id, dialog):
        """标记为已掌握"""
        self.db.mark_as_mastered(word_id)
        messagebox.showinfo("成功", "已标记为彻底记住")
        dialog.destroy()
        self.show_wrong_words()
    
    def clear_wrong_words(self, dialog):
        """清空错词本"""
        if messagebox.askyesno("确认", "确定要清空错词本吗？"):
            self.db.clear_wrong_words()
            messagebox.showinfo("成功", "错词本已清空")
            dialog.destroy()
            self.show_wrong_words()
    
    def show_levels(self):
        """显示关卡列表 - 按计划规划关卡"""
        # 获取所有计划
        campaigns = self.level_sys.get_all_campaigns()
        
        if not campaigns:
            # 提示创建计划
            dialog = tk.Toplevel(self.root)
            dialog.title("提示")
            dialog.geometry("450x300")
            dialog.configure(bg="#FFFACD")
            
            tk.Label(dialog, text="📋 还没有学习计划",
                    font=("Microsoft YaHei", 20, "bold"),
                    bg="#FFFACD", fg="#FF6347").pack(pady=20)
            
            tk.Label(dialog, text="要进入关卡模式，您需要先创建一个学习计划。\n\n学习计划会将单词分成多个关卡，\n让您可以按计划系统地学习。",
                    font=("Microsoft YaHei", 13),
                    bg="#FFFACD", fg="#333333",
                    justify=tk.CENTER).pack(pady=10)
            
            btn_frame = tk.Frame(dialog, bg="#FFFACD")
            btn_frame.pack(pady=20)
            
            tk.Button(btn_frame, text="📝 创建学习计划",
                     font=("Microsoft YaHei", 14, "bold"),
                     bg="#4CAF50", fg="white",
                     relief=tk.RAISED, bd=3,
                     padx=20, pady=10,
                     command=lambda: [dialog.destroy(), self.show_smart_plan()]).pack(side=tk.LEFT, padx=10)
            
            tk.Button(btn_frame, text="🔙 返回",
                     font=("Microsoft YaHei", 14, "bold"),
                     bg="#9E9E9E", fg="white",
                     relief=tk.RAISED, bd=3,
                     padx=20, pady=10,
                     command=dialog.destroy).pack(side=tk.LEFT, padx=10)
            return
        
        # 选择计划对话框
        select_win = tk.Toplevel(self.root)
        select_win.title("选择学习计划")
        select_win.geometry("500x400")
        select_win.configure(bg="#87CEEB")
        
        tk.Label(select_win, text="🏆 选择学习计划",
                font=("Microsoft YaHei", 20, "bold"),
                bg="#87CEEB", fg="#FFD700").pack(pady=15)
        
        # 计划列表
        plan_var = tk.StringVar()
        
        for campaign in campaigns:
            plan_text = f"{campaign['campaign_name']} ({campaign.get('grade_level', '自定义')}) - {campaign['total_levels']}关"
            rb = tk.Radiobutton(select_win, text=plan_text,
                               variable=plan_var, value=campaign['campaign_name'],
                               font=("Microsoft YaHei", 12),
                               bg="#87CEEB")
            rb.pack(anchor=tk.W, padx=20, pady=5)
        
        if campaigns:
            plan_var.set(campaigns[0]['campaign_name'])
        
        def show_campaign_levels():
            campaign_name = plan_var.get()
            if not campaign_name:
                messagebox.showwarning("警告", "请选择一个计划")
                return
            
            select_win.destroy()
            self.show_level_grid(campaign_name)
        
        tk.Button(select_win, text="开始挑战",
                 font=("Microsoft YaHei", 14, "bold"),
                 bg="#4CAF50", fg="white",
                 relief=tk.RAISED, bd=3,
                 padx=20, pady=10,
                 command=show_campaign_levels).pack(pady=15)
        
        tk.Button(select_win, text="取消",
                 font=("Microsoft YaHei", 12),
                 bg="#FFB6C1", fg="#DC143C",
                 relief=tk.RAISED, bd=3,
                 padx=15, pady=7,
                 command=select_win.destroy).pack(pady=5)
    
    def show_level_grid(self, campaign_name):
        """显示指定计划的关卡网格"""
        levels = self.db.fetchall(
            "SELECT * FROM levels WHERE campaign_name = ? ORDER BY level_number",
            (campaign_name,)
        )
        levels = [dict(row) for row in levels]
        
        if not levels:
            messagebox.showinfo("提示", "该计划没有关卡")
            return

        level_win = tk.Toplevel(self.root)
        level_win.title(f"🏆 {campaign_name}")
        level_win.geometry("900x700")
        level_win.configure(bg="#87CEEB")

        tk.Label(level_win, text=f"🏆 {campaign_name}",
                font=("Microsoft YaHei", 26, "bold"),
                bg="#87CEEB", fg="#FFD700").pack(pady=12)

        # 关卡网格
        grid_frame = tk.Frame(level_win, bg="#87CEEB")
        grid_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=12)

        # 每行显示4个关卡
        row = 0
        col = 0
        for level in levels:
            icon, desc = self.level_sys.get_level_status_icon(level)

            color = "#9E9E9E" if not level['unlocked'] else \
                   "#FFD700" if level['best_accuracy'] >= 100 else \
                   "#4CAF50" if level['best_accuracy'] >= 90 else \
                   "#FF9800" if level['best_accuracy'] > 0 else "#2196F3"

            level_btn = tk.Frame(grid_frame, bg=color, relief=tk.RAISED, bd=3)
            level_btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            tk.Label(level_btn, text=f"第{level['level_number']}关",
                    font=("Microsoft YaHei", 15, "bold"),
                    bg=color, fg="white").pack(pady=5)

            tk.Label(level_btn, text=icon,
                    font=("Microsoft YaHei", 26),
                    bg=color).pack(pady=5)

            tk.Label(level_btn, text=desc,
                    font=("Microsoft YaHei", 11),
                    bg=color, fg="white").pack(pady=2)

            if level['best_score'] > 0:
                tk.Label(level_btn,
                        text=f"最佳: {level['best_score']}分 ({level['best_accuracy']:.0f}%)",
                        font=("Microsoft YaHei", 10),
                        bg=color, fg="white").pack(pady=2)

            if level['unlocked']:
                tk.Button(level_btn, text="进入",
                         font=("Microsoft YaHei", 11, "bold"),
                         bg="#90EE90", fg="#2E8B57",
                         relief=tk.RAISED,
                         bd=2,
                         padx=10,
                         pady=4,
                         command=lambda lid=level['id']: self.enter_level(lid, level_win)).pack(pady=5)

            col += 1
            if col > 3:
                col = 0
                row += 1

        tk.Button(level_win, text="关闭",
                 font=("Microsoft YaHei", 13, "bold"),
                 bg="#FFB6C1", fg="#DC143C",
                 relief=tk.RAISED,
                 bd=3,
                 padx=18,
                 pady=7,
                 command=level_win.destroy).pack(pady=12)
    
    def enter_level(self, level_id, parent_win):
        """进入关卡"""
        detail = self.level_sys.get_level_detail(level_id)
        if not detail:
            return
        
        words = detail['words']
        if not words:
            messagebox.showwarning("警告", "该关卡没有单词")
            return
        
        parent_win.destroy()
        
        def on_level_complete(result):
            if result:
                # 更新关卡状态
                self.db.update_level_status(level_id, result['accuracy'], result['score'])
                self.db.record_level_attempt(
                    level_id,
                    result['correct'] + result['wrong'],
                    result['correct'],
                    result['score'],
                    result['accuracy'],
                    result['duration']
                )
                
                # 记录每日打卡
                today = datetime.now().strftime("%Y-%m-%d")
                self.db.record_daily_checkin(
                    today,
                    0,  # 复习单词数（简化）
                    0,
                    result['correct'],
                    result['wrong'],
                    result['accuracy'],
                    result['duration']
                )
                
                # 记录学习场次
                import uuid
                session_id = str(uuid.uuid4())[:8]
                self.db.save_learning_session(
                    session_id,
                    result['correct'] + result['wrong'],
                    result['correct'],
                    result['wrong'],
                    result['duration'],
                    None,
                    "level"
                )
            
            self.create_main_menu()
        
        self.show_preview_window(words, 
                                lambda: self.start_level_game(words, on_level_complete))
    
    def start_level_game(self, words, callback):
        """开始关卡游戏"""
        mode = self.game_mode.get()
        total = self.words_per_round.get()
        
        self.game_engine = GameEngine(self.root, self.db, self.sound, self.images)
        self.game_engine.start_game(words, mode, total, callback, None, None)
    
    def show_calendar(self):
        """显示学习日历"""
        cal_view = CalendarView(self.root, self.db)
        cal_view.show_calendar_window()
    
    def show_statistics(self):
        """显示学习统计"""
        stats_win = tk.Toplevel(self.root)
        stats_win.title("📊 学习统计")
        stats_win.geometry("1100x950")
        stats_win.configure(bg="#87CEEB")
        
        tk.Label(stats_win, text="📊 学习统计",
                font=("Microsoft YaHei", 24, "bold"),
                bg="#87CEEB", fg="#2E8B57").pack(pady=10)
        
        # 统计模式选择
        mode_frame = tk.Frame(stats_win, bg="#87CEEB")
        mode_frame.pack(pady=5)
        
        stat_mode = tk.StringVar(value="date")
        
        tk.Radiobutton(mode_frame, text="📅 按日期统计",
                      variable=stat_mode, value="date",
                      font=("Microsoft YaHei", 12),
                      bg="#87CEEB",
                      command=lambda: self.update_statistics_charts(stats_win, stat_mode.get())).pack(side=tk.LEFT, padx=15)
        
        tk.Radiobutton(mode_frame, text="🎮 按学习场次统计",
                      variable=stat_mode, value="session",
                      font=("Microsoft YaHei", 12),
                      bg="#87CEEB",
                      command=lambda: self.update_statistics_charts(stats_win, stat_mode.get())).pack(side=tk.LEFT, padx=15)
        
        # 图表容器
        chart_frame = tk.Frame(stats_win, bg="#87CEEB")
        chart_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        # 保存图表框架引用
        stats_win.chart_frame = chart_frame
        
        # 初始加载
        self.update_statistics_charts(stats_win, "date")
        
        tk.Button(stats_win, text="关闭",
                 font=("Microsoft YaHei", 12, "bold"),
                 bg="#FFB6C1", fg="#DC143C",
                 relief=tk.RAISED,
                 bd=3,
                 padx=15,
                 pady=5,
                 command=stats_win.destroy).pack(pady=10)
    
    def update_statistics_charts(self, stats_win, mode):
        """更新统计图表"""
        # 清除旧图表
        for widget in stats_win.chart_frame.winfo_children():
            widget.destroy()
        
        # 根据模式获取数据
        if mode == "date":
            daily_stats = self.db.get_last_30_days_stats()
            print(f"[DEBUG] daily_stats: {daily_stats}")
            self._create_date_charts(stats_win.chart_frame, daily_stats)
        else:
            session_stats = self.db.get_session_stats()
            print(f"[DEBUG] session_stats: {session_stats}")
            self._create_session_charts(stats_win.chart_frame, session_stats)
    
    def _create_date_charts(self, chart_frame, daily_stats):
        """创建按日期的图表"""
        # 正确率趋势图
        try:
            trend_path = "accuracy_trend.png"
            if StatisticsGenerator.generate_accuracy_trend(daily_stats, trend_path):
                from PIL import Image, ImageTk
                img = Image.open(trend_path)
                img = img.resize((480, 280), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(chart_frame, image=photo, bg="#87CEEB")
                label.image = photo
                label.grid(row=0, column=0, padx=10, pady=10)
                tk.Label(chart_frame, text="📈 正确率趋势（按日期）", font=("Microsoft YaHei", 11, "bold"), 
                        bg="#87CEEB", fg="#2E8B57").grid(row=1, column=0, padx=10, pady=5)
        except Exception as e:
            print(f"显示趋势图失败: {e}")
        
        # 学习时长分布图
        try:
            duration_path = "study_duration.png"
            if StatisticsGenerator.generate_study_duration_chart(daily_stats, days=7, save_path=duration_path):
                from PIL import Image, ImageTk
                img = Image.open(duration_path)
                img = img.resize((480, 280), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(chart_frame, image=photo, bg="#87CEEB")
                label.image = photo
                label.grid(row=0, column=1, padx=10, pady=10)
                tk.Label(chart_frame, text="⏱️ 学习时长分布（按日期）", font=("Microsoft YaHei", 11, "bold"), 
                        bg="#87CEEB", fg="#2196F3").grid(row=1, column=1, padx=10, pady=5)
        except Exception as e:
            print(f"显示时长图失败: {e}")
        
        # 错词下降曲线
        try:
            wrong_path = "wrong_words_trend.png"
            wrong_words_history = []
            for stat in daily_stats:
                if stat.get('wrong_count', 0) > 0:
                    wrong_words_history.append((stat['date'], stat['wrong_count']))
            if StatisticsGenerator.generate_wrong_words_trend(wrong_words_history, wrong_path):
                from PIL import Image, ImageTk
                img = Image.open(wrong_path)
                img = img.resize((480, 280), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(chart_frame, image=photo, bg="#87CEEB")
                label.image = photo
                label.grid(row=2, column=0, padx=10, pady=10)
                tk.Label(chart_frame, text="📉 错词下降曲线（按日期）", font=("Microsoft YaHei", 11, "bold"), 
                        bg="#87CEEB", fg="#F44336").grid(row=3, column=0, padx=10, pady=5)
        except Exception as e:
            print(f"显示错词图失败: {e}")
        
        # 学习热力图
        try:
            heatmap_path = "heatmap.png"
            heatmap_data = {}
            for stat in daily_stats:
                total = stat.get('new_words_count', 0) + stat.get('review_words_count', 0)
                if total > 0:
                    heatmap_data[stat['date']] = total
            now = datetime.now()
            if StatisticsGenerator.generate_heatmap(heatmap_data, now.year, now.month, heatmap_path):
                from PIL import Image, ImageTk
                img = Image.open(heatmap_path)
                img = img.resize((480, 280), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(chart_frame, image=photo, bg="#87CEEB")
                label.image = photo
                label.grid(row=2, column=1, padx=10, pady=10)
                tk.Label(chart_frame, text="🔥 学习热力图（按日期）", font=("Microsoft YaHei", 11, "bold"), 
                        bg="#87CEEB", fg="#FF9800").grid(row=3, column=1, padx=10, pady=5)
        except Exception as e:
            print(f"显示热力图失败: {e}")
    
    def _create_session_charts(self, chart_frame, session_stats):
        """创建按学习场次的图表"""
        # 正确率趋势图（按场次）
        try:
            trend_path = "session_accuracy_trend.png"
            if StatisticsGenerator.generate_session_accuracy_trend(session_stats, trend_path):
                from PIL import Image, ImageTk
                img = Image.open(trend_path)
                img = img.resize((480, 280), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(chart_frame, image=photo, bg="#87CEEB")
                label.image = photo
                label.grid(row=0, column=0, padx=10, pady=10)
                tk.Label(chart_frame, text="📈 正确率趋势（按场次）", font=("Microsoft YaHei", 11, "bold"), 
                        bg="#87CEEB", fg="#2E8B57").grid(row=1, column=0, padx=10, pady=5)
        except Exception as e:
            print(f"显示场次趋势图失败: {e}")
        
        # 学习时长分布图（按场次）
        try:
            duration_path = "session_duration.png"
            if StatisticsGenerator.generate_session_duration_chart(session_stats, save_path=duration_path):
                from PIL import Image, ImageTk
                img = Image.open(duration_path)
                img = img.resize((480, 280), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(chart_frame, image=photo, bg="#87CEEB")
                label.image = photo
                label.grid(row=0, column=1, padx=10, pady=10)
                tk.Label(chart_frame, text="⏱️ 学习时长分布（按场次）", font=("Microsoft YaHei", 11, "bold"), 
                        bg="#87CEEB", fg="#2196F3").grid(row=1, column=1, padx=10, pady=5)
        except Exception as e:
            print(f"显示场次时长图失败: {e}")
        
        # 错词下降曲线（按场次）
        try:
            wrong_path = "session_wrong_trend.png"
            wrong_history = []
            for stat in session_stats:
                if stat.get('wrong_count', 0) > 0:
                    # 包含 session_id, wrong_count, total_count, end_time
                    wrong_history.append({
                        'session_id': stat.get('session_id', 'N/A'),
                        'wrong_count': stat.get('wrong_count', 0),
                        'total_count': stat.get('total_count', stat.get('correct_count', 0) + stat.get('wrong_count', 0)),
                        'end_time': stat.get('end_time', '')
                    })
            if StatisticsGenerator.generate_session_wrong_trend(wrong_history, wrong_path):
                from PIL import Image, ImageTk
                img = Image.open(wrong_path)
                img = img.resize((480, 280), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(chart_frame, image=photo, bg="#87CEEB")
                label.image = photo
                label.grid(row=2, column=0, padx=10, pady=10)
                tk.Label(chart_frame, text="📉 错词下降曲线（按场次）", font=("Microsoft YaHei", 11, "bold"), 
                        bg="#87CEEB", fg="#F44336").grid(row=3, column=0, padx=10, pady=5)
        except Exception as e:
            print(f"显示场次错词图失败: {e}")
        
        # 学习进度图（按场次）
        try:
            progress_path = "session_progress.png"
            if StatisticsGenerator.generate_session_progress_chart(session_stats, save_path=progress_path):
                from PIL import Image, ImageTk
                img = Image.open(progress_path)
                img = img.resize((480, 280), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(chart_frame, image=photo, bg="#87CEEB")
                label.image = photo
                label.grid(row=2, column=1, padx=10, pady=10)
                tk.Label(chart_frame, text="📊 学习进度（按场次）", font=("Microsoft YaHei", 11, "bold"), 
                        bg="#87CEEB", fg="#9C27B0").grid(row=3, column=1, padx=10, pady=5)
        except Exception as e:
            print(f"显示场次进度图失败: {e}")
    
    def change_image(self):
        """更换游戏图片"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🖼️ 更换游戏图片")
        dialog.geometry("400x350")
        dialog.configure(bg="#87CEEB")
        
        tk.Label(dialog, text="选择要更换的图片",
                font=("Arial", 18, "bold"),
                bg="#87CEEB", fg="#2E8B57").pack(pady=15)
        
        btn_frame = tk.Frame(dialog, bg="#87CEEB")
        btn_frame.pack(pady=15)
        
        def select_image(image_type):
            filename = filedialog.askopenfilename(
                title=f"选择{image_type}图片",
                filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp")]
            )
            if filename:
                if self.images.change_image(image_type, filename):
                    messagebox.showinfo("成功", f"{image_type}图片已更换！")
                    dialog.destroy()
                    self.create_main_menu()
        
        tk.Button(btn_frame, text="🐭 更换地鼠图片",
                 font=("Arial", 12, "bold"), width=18,
                 bg="#FFE4B5", fg="#8B6914",
                 relief=tk.RAISED, bd=3,
                 padx=10, pady=5,
                 command=lambda: select_image("mouse")).pack(pady=8)
        
        tk.Button(btn_frame, text="🔨 更换锤子图片",
                 font=("Arial", 12, "bold"), width=18,
                 bg="#FFDAB9", fg="#FF6347",
                 relief=tk.RAISED, bd=3,
                 padx=10, pady=5,
                 command=lambda: select_image("hammer")).pack(pady=8)
        
        tk.Button(btn_frame, text="💨 更换逃跑图片",
                 font=("Arial", 12, "bold"), width=18,
                 bg="#E6E6FA", fg="#4B0082",
                 relief=tk.RAISED, bd=3,
                 padx=10, pady=5,
                 command=lambda: select_image("runaway")).pack(pady=8)
        
        tk.Button(btn_frame, text="😵 更换受伤图片",
                 font=("Arial", 12, "bold"), width=18,
                 bg="#AFEEEE", fg="#008B8B",
                 relief=tk.RAISED, bd=3,
                 padx=10, pady=5,
                 command=lambda: select_image("injured")).pack(pady=8)
        
        tk.Button(dialog, text="关闭",
                 font=("Arial", 12, "bold"),
                 bg="#AFEEEE", fg="#008B8B",
                 relief=tk.RAISED,
                 bd=3,
                 padx=15,
                 pady=5,
                 command=dialog.destroy).pack(pady=10)
    
    def show_smart_plan(self):
        """显示智能学习计划设置"""
        dialog = tk.Toplevel(self.root)
        dialog.title("📋 智能学习计划")
        dialog.geometry("600x500")
        dialog.configure(bg="#FFFACD")  # 柠檬绸色背景

        tk.Label(dialog, text="📋 创建智能学习计划",
                font=("Microsoft YaHei", 22, "bold"),
                bg="#FFFACD", fg="#DAA520").pack(pady=15)

        # 战役名称
        tk.Label(dialog, text="计划名称：",
                font=("Microsoft YaHei", 13),
                bg="#FFFACD").pack(pady=5)

        campaign_name = tk.Entry(dialog, font=("Microsoft YaHei", 13), width=35)
        campaign_name.pack(pady=5)
        campaign_name.insert(0, f"{self.current_grade.get()}学习计划")

        # 选项面板容器
        options_frame = tk.Frame(dialog, bg="#FFFACD")
        options_frame.pack(pady=5, fill=tk.X, padx=40)

        # 年级选择面板（仅内置单词时显示）
        grade_panel = tk.Frame(options_frame, bg="#E8F5E9")

        tk.Label(grade_panel, text="选择年级：",
                font=("Microsoft YaHei", 13),
                bg="#E8F5E9",
                fg="#2E7D32").pack(side=tk.LEFT, padx=10)

        grade_var = tk.StringVar(value=self.current_grade.get())
        grade_combo = ttk.Combobox(grade_panel, textvariable=grade_var,
                                  values=self.word_mgr.get_all_grades(),
                                  font=("Microsoft YaHei", 13), width=20)
        grade_combo.pack(side=tk.LEFT, padx=10)

        # 年级单词数标签
        grade_word_count_label = tk.Label(grade_panel, text="",
                                        font=("Microsoft YaHei", 12),
                                        bg="#E8F5E9",
                                        fg="#FF6347")
        grade_word_count_label.pack(side=tk.LEFT, padx=10)

        # 自定义单词面板
        custom_panel = tk.Frame(options_frame, bg="#E3F2FD")

        custom_file_label = tk.Label(custom_panel, text="未选择文件",
                                    font=("Microsoft YaHei", 11),
                                    bg="#E3F2FD", fg="#FF6347")
        custom_file_label.pack(pady=5)

        custom_file_path = [None]  # 使用列表以便在闭包中修改

        def select_custom_file():
            filename = filedialog.askopenfilename(
                title="选择自定义单词本",
                filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv")]
            )
            if filename:
                custom_file_path[0] = filename
                custom_file_label.config(text=f"已选择: {os.path.basename(filename)}")

        tk.Button(custom_panel, text="📁 选择自定义单词本",
                 font=("Microsoft YaHei", 12),
                 bg="#FFDAB9", fg="#FF6347",
                 relief=tk.RAISED, bd=3,
                 padx=12, pady=6,
                 command=select_custom_file).pack(pady=5)

        def on_source_selected(source):
            """根据来源选择显示对应面板"""
            grade_panel.pack_forget()
            custom_panel.pack_forget()
            
            if source == "builtin":
                grade_panel.pack(fill=tk.X, padx=20, pady=5)
                # 更新年级单词数
                grade = grade_var.get()
                words = self.word_mgr.get_words_for_grade(grade)
                if words:
                    grade_word_count_label.config(text=f"📖 {len(words)} 个单词", fg="#4CAF50")
                else:
                    grade_word_count_label.config(text="⚠️ 该年级暂无单词", fg="#FF6347")
            else:
                custom_panel.pack(fill=tk.X, padx=20, pady=5)

        # 单词来源选择 - 在函数定义之后创建
        source_frame = tk.Frame(dialog, bg="#FFFACD")
        source_frame.pack(pady=10)

        word_source = tk.StringVar(value="builtin")
        tk.Radiobutton(source_frame, text="📚 使用系统内置年级单词",
                      variable=word_source, value="builtin",
                      font=("Microsoft YaHei", 13),
                      bg="#FFFACD",
                      command=lambda: on_source_selected("builtin")).pack(anchor=tk.W, padx=20)

        tk.Radiobutton(source_frame, text="📁 使用自定义导入的单词本",
                      variable=word_source, value="custom",
                      font=("Microsoft YaHei", 13),
                      bg="#FFFACD",
                      command=lambda: on_source_selected("custom")).pack(anchor=tk.W, padx=20)

        # 初始显示年级面板
        options_frame.after(50, lambda: on_source_selected("builtin"))

        # 天数设置
        tk.Label(dialog, text="计划完成天数：",
                font=("Microsoft YaHei", 13),
                bg="#FFFACD").pack(pady=5)

        days_var = tk.IntVar(value=30)
        tk.Spinbox(dialog, from_=7, to=90, width=12,
                  font=("Microsoft YaHei", 13),
                  textvariable=days_var).pack(pady=5)
        
        def create_plan():
            name = campaign_name.get().strip()
            if not name:
                messagebox.showwarning("警告", "请输入计划名称")
                return
            
            days = days_var.get()
            source = word_source.get()
            
            if source == "builtin":
                # 使用内置年级单词
                grade = grade_var.get()
                words = self.word_mgr.get_words_for_grade(grade)
                if not words:
                    messagebox.showwarning("警告", f"{grade} 没有单词，请先导入词库到wordlists文件夹")
                    return
                
                # 创建战役
                result = self.level_sys.create_campaign(name, grade, days)
                if result:
                    self.latest_plan = {
                        'name': name,
                        'grade': grade,
                        'total_words': result['total_words'],
                        'daily_words': result['daily_words'],
                        'levels': result['levels'],
                        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    messagebox.showinfo("成功", 
                                       f"计划创建成功！\n"
                                       f"单词来源: 系统内置 ({grade})\n"
                                       f"总单词: {result['total_words']}个\n"
                                       f"每天学习: {result['daily_words']}个\n"
                                       f"预计用时: {result['estimated_time_per_day']:.0f}分钟/天\n"
                                       f"共 {len(result['levels'])} 关\n\n"
                                       f"点击'开始学习'将使用此计划")
                    dialog.destroy()
                    self.create_main_menu()  # 刷新主界面
                else:
                    messagebox.showerror("错误", "创建计划失败")
            else:
                # 使用自定义单词
                if not custom_file_path[0]:
                    messagebox.showwarning("警告", "请先选择自定义单词本文件")
                    return
                
                # 导入自定义单词
                count = self.word_mgr.import_custom_wordlist(custom_file_path[0])
                if count == 0:
                    messagebox.showerror("错误", "导入单词失败，请检查文件格式")
                    return
                
                # 获取自定义单词
                custom_words = self.db.get_custom_words()
                if not custom_words:
                    messagebox.showwarning("警告", "没有可用的自定义单词")
                    return
                
                # 为自定义单词创建关卡
                total_words = len(custom_words)
                daily_words = math.ceil(total_words / days)
                
                print(f"创建自定义战役: {name}")
                print(f"总单词数: {total_words}, 每天学习: {daily_words}个, 天数: {days}")
                
                # 按天拆分单词
                levels_data = []
                for i in range(0, total_words, daily_words):
                    day_words = custom_words[i:i+daily_words]
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
                        name,
                        word_ids,
                        'custom',     # 自定义单词
                        daily_words   # 每日单词数
                    )
                    created_levels.append({
                        'level_id': level_id,
                        'level_number': level_data['level_number'],
                        'word_count': len(word_ids)
                    })
                
                estimated_time = daily_words * 1.5
                
                self.latest_plan = {
                    'name': name,
                    'grade': 'custom',
                    'total_words': total_words,
                    'daily_words': daily_words,
                    'levels': created_levels,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                messagebox.showinfo("成功", 
                                   f"计划创建成功！\n"
                                   f"单词来源: 自定义导入\n"
                                   f"总单词: {total_words}个\n"
                                   f"每天学习: {daily_words}个\n"
                                   f"预计用时: {estimated_time:.0f}分钟/天\n"
                                   f"共 {len(created_levels)} 关\n\n"
                                   f"点击'开始学习'将使用此计划")
                dialog.destroy()
                self.create_main_menu()  # 刷新主界面
        
        tk.Button(dialog, text="✨ 创建计划",
                 font=("Microsoft YaHei", 15, "bold"),
                 bg="#90EE90", fg="#2E8B57",
                 relief=tk.RAISED, bd=4,
                 padx=22, pady=9,
                 command=create_plan).pack(pady=20)

        tk.Button(dialog, text="取消",
                 font=("Microsoft YaHei", 13),
                 bg="#FFB6C1", fg="#DC143C",
                 relief=tk.RAISED, bd=3,
                 padx=18, pady=7,
                 command=dialog.destroy).pack(pady=5)
    
    def show_my_plans(self):
        """显示我的学习计划"""
        dialog = tk.Toplevel(self.root)
        dialog.title("📑 我的学习计划")
        dialog.geometry("800x600")
        dialog.configure(bg="#E0FFFF")  # 淡青色背景

        tk.Label(dialog, text="📑 我的学习计划",
                font=("Microsoft YaHei", 22, "bold"),
                bg="#E0FFFF", fg="#008B8B").pack(pady=15)

        # 获取所有战役
        campaigns = self.level_sys.get_all_campaigns()
        
        if not campaigns:
            tk.Label(dialog, text="暂无学习计划",
                    font=("Microsoft YaHei", 18),
                    bg="#E0FFFF", fg="#666666").pack(pady=20)
            
            tk.Label(dialog, text="点击下方按钮创建您的第一个学习计划",
                    font=("Microsoft YaHei", 13),
                    bg="#E0FFFF", fg="#888888").pack(pady=5)
            
            btn_frame = tk.Frame(dialog, bg="#E0FFFF")
            btn_frame.pack(pady=20)
            
            tk.Button(btn_frame, text="📝 创建学习计划",
                     font=("Microsoft YaHei", 14, "bold"),
                     bg="#4CAF50", fg="white",
                     relief=tk.RAISED, bd=3,
                     padx=20, pady=10,
                     command=lambda: [dialog.destroy(), self.show_smart_plan()]).pack(side=tk.LEFT, padx=10)
            
            tk.Button(btn_frame, text="关闭",
                     font=("Microsoft YaHei", 13),
                     bg="#FFB6C1", fg="#DC143C",
                     relief=tk.RAISED, bd=3,
                     padx=18, pady=7,
                     command=dialog.destroy).pack(side=tk.LEFT, padx=10)
            return

        # 创建计划列表框架
        list_frame = tk.Frame(dialog, bg="#E0FFFF")
        list_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

        # 表头
        headers = ["计划名称", "年级", "关卡数", "完成进度", "操作"]
        widths = [20, 10, 10, 12, 12]
        
        header_frame = tk.Frame(list_frame, bg="#008B8B")
        header_frame.pack(fill=tk.X)
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            tk.Label(header_frame, text=header,
                    font=("Microsoft YaHei", 12, "bold"),
                    bg="#008B8B", fg="white",
                    width=width, anchor="center").pack(side=tk.LEFT, padx=1, pady=2)

        # 显示每个计划
        for campaign in campaigns:
            row_frame = tk.Frame(list_frame, bg="#FFFFFF" if campaigns.index(campaign) % 2 == 0 else "#F5F5F5")
            row_frame.pack(fill=tk.X, pady=1)
            
            # 计算完成进度
            total_levels = campaign['total_levels']
            completed_levels = len([l for l in campaign.get('levels', []) if l.get('status') == 'completed'])
            progress = f"{completed_levels}/{total_levels}"
            
            row_data = [
                campaign['campaign_name'],
                campaign.get('grade_level', '自定义'),
                str(total_levels),
                progress
            ]
            
            for i, (data, width) in enumerate(zip(row_data, widths[:4])):
                tk.Label(row_frame, text=data,
                        font=("Microsoft YaHei", 11),
                        bg=row_frame.cget('bg'),
                        width=width, anchor="center").pack(side=tk.LEFT, padx=1, pady=5)
            
            # 操作按钮
            btn_frame = tk.Frame(row_frame, bg=row_frame.cget('bg'))
            btn_frame.pack(side=tk.LEFT, padx=5)
            
            tk.Button(btn_frame, text="应用",
                    font=("Microsoft YaHei", 10),
                    bg="#2196F3", fg="white",
                    relief=tk.RAISED, bd=2,
                    padx=8, pady=2,
                    command=lambda c=campaign: self.apply_campaign(c, dialog)).pack(side=tk.LEFT, padx=2)
            
            tk.Button(btn_frame, text="查看详情",
                    font=("Microsoft YaHei", 10),
                    bg="#4CAF50", fg="white",
                    relief=tk.RAISED, bd=2,
                    padx=8, pady=2,
                    command=lambda c=campaign: self.show_campaign_detail(c)).pack(side=tk.LEFT, padx=2)
            
            tk.Button(btn_frame, text="删除",
                    font=("Microsoft YaHei", 10),
                    bg="#F44336", fg="white",
                    relief=tk.RAISED, bd=2,
                    padx=8, pady=2,
                    command=lambda c=campaign: self.delete_campaign(c, list_frame)).pack(side=tk.LEFT, padx=2)

        tk.Button(dialog, text="关闭",
                 font=("Microsoft YaHei", 13),
                 bg="#FFB6C1", fg="#DC143C",
                 relief=tk.RAISED, bd=3,
                 padx=18, pady=7,
                 command=dialog.destroy).pack(pady=15)
    
    def show_campaign_detail(self, campaign):
        """显示战役详情"""
        detail_win = tk.Toplevel(self.root)
        detail_win.title(f"📋 {campaign['campaign_name']}")
        detail_win.geometry("700x500")
        detail_win.configure(bg="#E0FFFF")

        tk.Label(detail_win, text=f"📋 {campaign['campaign_name']}",
                font=("Microsoft YaHei", 20, "bold"),
                bg="#E0FFFF", fg="#008B8B").pack(pady=10)

        # 战役信息
        info_text = f"年级: {campaign.get('grade_level', '自定义')}\n"
        info_text += f"总关卡: {campaign['total_levels']} 关\n"
        info_text += f"创建时间: {campaign.get('created_at', '未知')}"
        
        tk.Label(detail_win, text=info_text,
                font=("Microsoft YaHei", 12),
                bg="#E0FFFF", fg="#333333",
                justify=tk.LEFT).pack(pady=10)

        # 关卡列表
        levels_frame = tk.Frame(detail_win, bg="#E0FFFF")
        levels_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

        tk.Label(levels_frame, text="关卡列表:",
                font=("Microsoft YaHei", 13, "bold"),
                bg="#E0FFFF", fg="#008B8B").pack(anchor=tk.W, pady=5)

        for level in campaign.get('levels', []):
            status_icon = "✅" if level.get('status') == 'completed' else "🔒" if level.get('status') == 'locked' else "🎮"
            status_text = f"  {status_icon} 关卡{level['level_number']}: {level.get('total_words', 0)}个单词"
            if level.get('best_accuracy'):
                status_text += f" - 最佳正确率: {level['best_accuracy']:.0f}%"
            
            tk.Label(levels_frame, text=status_text,
                    font=("Microsoft YaHei", 11),
                    bg="#E0FFFF", fg="#333333",
                    anchor=tk.W).pack(fill=tk.X, pady=2)

        tk.Button(detail_win, text="关闭",
                 font=("Microsoft YaHei", 13),
                 bg="#FFB6C1", fg="#DC143C",
                 relief=tk.RAISED, bd=3,
                 padx=18, pady=7,
                 command=detail_win.destroy).pack(pady=15)
    
    def apply_campaign(self, campaign, dialog):
        """应用选定的计划"""
        # 设置最新计划
        self.latest_plan = {
            'name': campaign['campaign_name'],
            'grade': campaign.get('grade_level', 'custom'),
            'total_words': campaign.get('total_levels', 0) * campaign.get('daily_words', 10),
            'daily_words': campaign.get('daily_words', 10),
            'levels': campaign.get('levels', []),
            'created_at': campaign.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        }
        
        # 切换到计划模式
        self.word_source.set("plan")
        
        # 关闭对话框
        dialog.destroy()
        
        # 刷新主界面
        self.create_main_menu()
        
        messagebox.showinfo("成功", f"已应用计划 '{campaign['campaign_name']}'！\n现在开始学习将使用此计划。")
    
    def delete_campaign(self, campaign, list_frame):
        """删除战役"""
        result = messagebox.askyesno("确认删除", f"确定要删除计划 '{campaign['campaign_name']}' 吗？\n此操作不可恢复。")
        if result:
            if self.level_sys.delete_campaign(campaign['campaign_name']):
                messagebox.showinfo("成功", "计划已删除")
                # 刷新列表
                self.show_my_plans()
            else:
                messagebox.showerror("错误", "删除计划失败")


def main():
    """主函数"""
    root = tk.Tk()
    game = WordWhackGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
