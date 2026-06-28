"""
游戏核心模块
实现打地鼠游戏的核心逻辑和界面
"""
import tkinter as tk
from tkinter import messagebox
import random
import time
from datetime import datetime


class GameEngine:
    """游戏引擎，管理游戏状态和流程"""
    
    def __init__(self, root, db, sound_manager, image_utils):
        self.root = root
        self.db = db
        self.sound = sound_manager
        self.images = image_utils
        
        # 游戏状态
        self.game_running = False
        self.score = 0
        self.total_questions = 0
        self.current_question = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.combo_count = 0
        self.combo_bonus = 0
        
        # 当前游戏数据
        self.mode = None  # eng2chn 或 chn2eng
        self.current_word = None
        self.correct_option_index = None
        self.word_list = []
        self.session_id = None
        self.start_time = None
        
        # UI组件
        self.mice_buttons = []
        self.hammer_label = None
        
        # 回调函数
        self.on_game_over_callback = None
    
    def start_game(self, word_list, mode="eng2chn", total_questions=20, callback=None, restart_callback=None, next_round_callback=None):
        """
        开始游戏
        
        Args:
            word_list: 单词列表
            mode: 游戏模式
            total_questions: 总题数
            callback: 游戏结束回调
            restart_callback: 重新开始回调（用于再来一次）
            next_round_callback: 下一轮回调（用于获取新单词）
        """
        print(f"[DEBUG] GameEngine.start_game called with {len(word_list) if word_list else 0} words")
        if not word_list:
            messagebox.showwarning("警告", "没有可用的单词！")
            return False
        
        self.word_list = word_list
        self.mode = mode
        self.total_questions = min(total_questions, len(word_list) * 2)
        self.current_question = 0
        self.score = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.combo_count = 0
        self.combo_bonus = 0
        self.game_running = True
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.start_time = time.time()
        self.on_game_over_callback = callback
        self.restart_callback = restart_callback
        self.next_round_callback = next_round_callback
        
        print("[DEBUG] Calling _clear_root_window")
        self._clear_root_window()
        print("[DEBUG] Calling create_game_ui")
        self.create_game_ui()
        print("[DEBUG] Calling next_question")
        self.next_question()
        
        return True
    
    def _clear_root_window(self):
        """清空根窗口上的所有游戏相关组件"""
        # 使用withdraw暂时隐藏而不是destroy，避免几何管理问题
        children = list(self.root.winfo_children())
        for widget in children:
            if not isinstance(widget, tk.Toplevel):
                try:
                    # 取消注册并隐藏
                    widget.pack_forget()
                    widget.grid_forget()
                    widget.place_forget()
                    widget.destroy()
                except tk.TclError:
                    pass
        # 处理待处理的待删除widget
        self.root.update()
    
    def create_game_ui(self):
        """创建游戏界面 - 儿童绘本风格"""
        # 确保图片已加载
        if not self.images.get_image("mouse"):
            print("警告: 地鼠图片未加载，尝试重新加载")
            self.images.load_all_images()
        
        mouse_img = self.images.get_image("mouse")
        hammer_img = self.images.get_image("hammer")
        bg_img = self.images.get_image("background")
        
        if not mouse_img:
            print("错误: 无法加载地鼠图片，将使用文本按钮")
        if not hammer_img:
            print("警告: 无法加载锤子图片，将不显示锤子")
        if not bg_img:
            print("警告: 无法加载背景图片")
        
        # 设置背景图片
        if bg_img:
            self.bg_label = tk.Label(self.root, image=bg_img)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            self.root.configure(bg="#87CEEB")
        
        # 顶部信息栏（可爱风格）
        info_frame = tk.Frame(self.root, bg="#FFFACD", bd=0)  # 柠檬绸色
        info_frame.pack(fill=tk.X, pady=12, padx=20)

        self.score_label = tk.Label(info_frame, text=f"得分: {self.score}",
                                   font=("Microsoft YaHei", 20, "bold"),
                                   bg="#FFFACD", fg="#FF6347")  # 橙红色
        self.score_label.pack(side=tk.LEFT, padx=20)

        self.combo_label = tk.Label(info_frame, text="",
                                   font=("Microsoft YaHei", 18, "bold"),
                                   bg="#FFFACD", fg="#FF1493")  # 深粉色
        self.combo_label.pack(side=tk.LEFT, padx=20)

        self.progress_label = tk.Label(info_frame,
                                      text=f"进度: 0/{self.total_questions}",
                                      font=("Microsoft YaHei", 20),
                                      bg="#FFFACD", fg="#2E8B57")  # 深绿色
        self.progress_label.pack(side=tk.RIGHT, padx=20)

        # 题目显示区（可爱风格）
        self.question_label = tk.Label(self.root, text="",
                                      font=("Microsoft YaHei", 34, "bold"),
                                      bg="#FFFACD", fg="#FF1493")  # 柠檬绸背景，深粉文字
        self.question_label.pack(pady=35)

        # 地鼠按钮区（2x2网格，圆角可爱风格）
        mice_frame = tk.Frame(self.root, bg="#FFFACD", bd=0)
        mice_frame.pack(expand=True)

        self.mice_buttons = []
        for i in range(4):
            # 如果有图片则使用图片，否则使用纯文本按钮
            if mouse_img:
                btn = tk.Button(mice_frame,
                              image=mouse_img,
                              text="",
                              compound="top",
                              font=("Microsoft YaHei", 12, "bold"),
                              width=130,
                              height=130,
                              bg="#FFE4B5",  # 鹿皮色背景
                              activebackground="#FFDAB9",  # 桃色活跃背景
                              relief=tk.RAISED,
                              bd=5,
                              wraplength=110,
                              command=lambda idx=i: self.check_answer(idx))
            else:
                # 没有图片时使用纯文本按钮
                btn = tk.Button(mice_frame,
                              text="选项",
                              font=("Microsoft YaHei", 15, "bold"),
                              width=15,
                              height=3,
                              bg="#FFE4B5",  # 鹿皮色背景
                              activebackground="#FFDAB9",  # 桃色活跃背景
                              relief=tk.RAISED,
                              bd=5,
                              command=lambda idx=i: self.check_answer(idx))
            btn.grid(row=i//2, column=i%2, padx=25, pady=25)
            self.mice_buttons.append(btn)

        # 锤子标签（只有图片存在时才创建）
        if hammer_img:
            self.hammer_label = tk.Label(self.root,
                                        image=hammer_img)
            self.hammer_label.place(x=-100, y=-100)

            # 绑定鼠标事件
            self.root.bind('<Motion>', self.move_hammer)
            self.root.bind('<Button-1>', self.on_click)
        else:
            self.hammer_label = None

        # 返回按钮（圆角可爱风格）
        tk.Button(self.root, text="🏠 返回菜单",
                 font=("Microsoft YaHei", 13, "bold"),
                 bg="#FFB6C1",  # 浅红色
                 fg="#DC143C",  # 深红色
                 relief=tk.RAISED,
                 bd=3,
                 padx=18,
                 pady=7,
                 command=self.back_to_menu).pack(pady=20)
    
    def move_hammer(self, event):
        """锤子跟随鼠标移动"""
        if self.game_running and self.hammer_label:
            try:
                # 获取锤子图片的实际尺寸
                hammer_img = self.images.get_image("hammer")
                if hammer_img:
                    w = hammer_img.width()
                    h = hammer_img.height()
                else:
                    w, h = 80, 80  # 默认尺寸
                
                # 计算锤子左上角位置，使锤子中心对准鼠标
                x = event.x_root - w // 2
                y = event.y_root - h // 2
                
                # 使用place放置锤子
                self.hammer_label.place(x=x, y=y)
            except Exception as e:
                # 如果出错，使用简单方式
                self.hammer_label.place(x=event.x_root - 40, y=event.y_root - 40)
    
    def on_click(self, event):
        """鼠标点击动画"""
        if not self.game_running or not self.hammer_label:
            return
        x, y = self.hammer_label.winfo_x(), self.hammer_label.winfo_y()
        self.hammer_label.place(x=x, y=y+15)
        self.root.after(50, lambda: self.hammer_label.place(x=x, y=y))
    
    def next_question(self):
        """下一题"""
        if self.current_question >= self.total_questions:
            self.game_over()
            return
        
        self.current_question += 1
        self.update_progress()
        
        # 随机选择单词
        self.current_word = random.choice(self.word_list)
        
        # 获取图片
        mouse_img = self.images.get_image("mouse")
        
        # 根据模式生成题目
        if self.mode == "eng2chn":
            question_text = f"🐭 {self.current_word['english']} 的中文意思是？"
            correct_option = random.choice(self._parse_meanings(self.current_word['chinese']))
            options = self._generate_options(correct_option, is_english=False)
            self.correct_option_index = options.index(correct_option)
            
            for i, btn in enumerate(self.mice_buttons):
                if mouse_img:
                    btn.config(text=options[i], 
                              image=mouse_img, 
                              compound="top", 
                              state=tk.NORMAL, 
                              bg="#FFE4B5", 
                              relief=tk.RAISED)
                else:
                    btn.config(text=options[i], 
                              state=tk.NORMAL, 
                              bg="#FFE4B5", 
                              relief=tk.RAISED)
        else:  # chn2eng
            current_chinese = random.choice(self._parse_meanings(self.current_word['chinese']))
            question_text = f'🐭 "{current_chinese}" 的英文是？'
            correct_option = self.current_word['english']
            options = self._generate_options(correct_option, is_english=True)
            self.correct_option_index = options.index(correct_option)
            
            for i, btn in enumerate(self.mice_buttons):
                if mouse_img:
                    btn.config(text=options[i], 
                              image=mouse_img, 
                              compound="top", 
                              state=tk.NORMAL, 
                              bg="#FFE4B5", 
                              relief=tk.RAISED)
                else:
                    btn.config(text=options[i], 
                              state=tk.NORMAL, 
                              bg="#FFE4B5", 
                              relief=tk.RAISED)
        
        self.question_label.config(text=question_text)
    
    def _parse_meanings(self, chinese_str):
        """解析中文释义"""
        if not chinese_str:
            return ["???"]
        meanings = [m.strip() for m in chinese_str.split(";") if m.strip()]
        return meanings if meanings else ["???"]
    
    def _generate_options(self, correct_option, is_english=False):
        """生成选项（1个正确 + 3个干扰）"""
        options = [correct_option]
        
        # 收集候选干扰项
        candidates = []
        if is_english:
            for w in self.word_list:
                if w['english'] != correct_option:
                    candidates.append(w['english'])
        else:
            for w in self.word_list:
                for meaning in self._parse_meanings(w['chinese']):
                    if meaning != correct_option:
                        candidates.append(meaning)
        
        # 去重并随机选择
        candidates = list(set(candidates))
        random.shuffle(candidates)
        
        for cand in candidates:
            if len(options) >= 4:
                break
            if cand not in options:
                options.append(cand)
        
        # 如果不够4个，用"???"填充
        while len(options) < 4:
            options.append("???")
        
        random.shuffle(options)
        return options
    
    def check_answer(self, idx):
        """检查答案"""
        if not self.game_running:
            return
        
        # 禁用所有按钮
        for btn in self.mice_buttons:
            btn.config(state=tk.DISABLED)
        
        # 记录响应时间（简化处理）
        response_time_ms = 2000  # 默认2秒
        
        if idx == self.correct_option_index:
            # 答对
            self.combo_count += 1
            self.combo_bonus = (self.combo_count // 5) * 5
            total_score = 10 + self.combo_bonus
            self.score += total_score
            self.correct_count += 1
            
            self.update_score()
            self.update_combo_display()
            self.sound.play_sound("correct")
            
            if self.combo_count > 0 and self.combo_count % 5 == 0:
                self.sound.play_sound("combo")
            
            # 记录学习
            self.db.record_learning(
                self.current_word['id'], 
                True, 
                response_time_ms, 
                self.session_id
            )
            
            self.play_hit_animation(idx, True)
        else:
            # 答错
            self.combo_count = 0
            self.combo_bonus = 0
            self.score = max(0, self.score - 5)
            self.wrong_count += 1
            
            self.update_score()
            self.update_combo_display()
            
            # 添加到错词本
            self.db.add_wrong_word(
                self.current_word['id'],
                self.current_word['english'],
                self.current_word['chinese']
            )
            
            # 记录学习
            self.db.record_learning(
                self.current_word['id'], 
                False, 
                response_time_ms, 
                self.session_id
            )
            
            self.sound.play_sound("wrong")
            self.play_hit_animation(idx, False)
            
            # 询问是否还要练习
            self.root.after(100, self.ask_extra_practice)
    
    def ask_extra_practice(self):
        """询问是否额外练习"""
        if messagebox.askyesno("额外练习", 
                              f"这个单词 \"{self.current_word['english']}\" 您还想多练几次吗？"):
            self.db.add_extra_practice(self.current_word['id'], 3)
    
    def play_hit_animation(self, button_idx, is_correct):
        """播放击中动画"""
        injured_img = self.images.get_image("injured")
        runaway_img = self.images.get_image("runaway")
        
        if is_correct:
            # 正确答案：绿色底色 + 老鼠受伤图片
            correct_btn = self.mice_buttons[button_idx]
            if injured_img:
                correct_btn.config(image=injured_img, 
                                 bg="#4CAF50",  # 绿色底色
                                 relief=tk.SUNKEN)
            else:
                correct_btn.config(text="✓ 正确", 
                                 bg="#4CAF50",  # 绿色底色
                                 fg="white",
                                 relief=tk.SUNKEN)
            self.root.after(500, lambda: self.reset_after_correct(button_idx))
        else:
            for btn in self.mice_buttons:
                if runaway_img:
                    btn.config(image=runaway_img, 
                             bg="#F44336",  # 红色底色表示错误
                             relief=tk.FLAT)
                else:
                    btn.config(text="✗ 错误", 
                             bg="#F44336", 
                             fg="white",
                             relief=tk.FLAT)
            self.root.after(600, self.reset_after_wrong)
    
    def reset_after_correct(self, button_idx):
        """答对后重置"""
        mouse_img = self.images.get_image("mouse")
        if mouse_img:
            self.mice_buttons[button_idx].config(image=mouse_img, 
                                                bg="#FFE4B5", 
                                                relief=tk.RAISED)
        else:
            self.mice_buttons[button_idx].config(bg="#FFE4B5", 
                                                relief=tk.RAISED)
        self.next_question()
    
    def reset_after_wrong(self):
        """答错后重置"""
        mouse_img = self.images.get_image("mouse")
        for btn in self.mice_buttons:
            if mouse_img:
                btn.config(image=mouse_img, 
                          bg="#FFE4B5", 
                          relief=tk.RAISED)
            else:
                btn.config(bg="#FFE4B5", 
                          relief=tk.RAISED)
        self.next_question()
    
    def update_score(self):
        """更新分数显示"""
        self.score_label.config(text=f"得分: {self.score}")
    
    def update_combo_display(self):
        """更新连击显示"""
        if self.combo_count >= 10:
            combo_text = f"🔥 {self.combo_count}连击! (+{self.combo_bonus}加成)"
            color = "#FF0000"
        elif self.combo_count >= 5:
            combo_text = f"⚡ {self.combo_count}连击! (+{self.combo_bonus}加成)"
            color = "#FF6347"
        elif self.combo_count >= 3:
            combo_text = f"✨ {self.combo_count}连击"
            color = "#FFD700"
        else:
            combo_text = ""
            color = "#FF6347"
        
        self.combo_label.config(text=combo_text, fg=color)
    
    def update_progress(self):
        """更新进度显示"""
        self.progress_label.config(text=f"进度: {self.current_question}/{self.total_questions}")
    
    def game_over(self):
        """游戏结束"""
        self.game_running = False
        
        # 计算时长
        duration = int(time.time() - self.start_time) if self.start_time else 0
        
        # 计算正确率
        accuracy = (self.correct_count / self.total_questions * 100) if self.total_questions > 0 else 0
        
        # 播放音效
        self.sound.play_sound("game_over")
        
        # 解绑鼠标事件
        self.root.unbind('<Motion>')
        self.root.unbind('<Button-1>')
        
        # 创建自定义结算窗口
        dialog = tk.Toplevel(self.root)
        dialog.title("🎮 游戏结束")
        dialog.geometry("500x400")
        dialog.configure(bg="#F5F5F5")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 结果数据
        result_data = {
            'score': self.score,
            'correct': self.correct_count,
            'wrong': self.wrong_count,
            'accuracy': accuracy,
            'duration': duration
        }
        
        # 标题
        tk.Label(dialog, text="🎉 游戏结束！ 🎉",
                font=("Microsoft YaHei", 24, "bold"),
                bg="#F5F5F5", fg="#FF6B6B").pack(pady=20)
        
        # 正确率评价
        if accuracy >= 90:
            comment = "太棒了！完美表现！🌟"
            comment_color = "#4CAF50"
        elif accuracy >= 70:
            comment = "不错，继续努力！💪"
            comment_color = "#FF9800"
        else:
            comment = "多练习几次会更好！📚"
            comment_color = "#2196F3"
        
        tk.Label(dialog, text=comment,
                font=("Microsoft YaHei", 16),
                bg="#F5F5F5", fg=comment_color).pack(pady=10)
        
        # 结果统计框
        result_frame = tk.Frame(dialog, bg="#FFFFFF", relief=tk.RAISED, bd=2)
        result_frame.pack(pady=20, padx=40, fill=tk.BOTH, expand=True)
        
        # 分数
        tk.Label(result_frame, text=f"得分: {self.score}",
                font=("Microsoft YaHei", 18),
                bg="#FFFFFF", fg="#333333").pack(pady=8)
        
        # 正确错误数
        tk.Label(result_frame, text=f"正确: {self.correct_count}  |  错误: {self.wrong_count}",
                font=("Microsoft YaHei", 16),
                bg="#FFFFFF", fg="#666666").pack(pady=5)
        
        # 正确率
        tk.Label(result_frame, text=f"正确率: {accuracy:.1f}%",
                font=("Microsoft YaHei", 16),
                bg="#FFFFFF", fg="#9C27B0").pack(pady=5)
        
        # 时长
        minutes = duration // 60
        seconds = duration % 60
        tk.Label(result_frame, text=f"用时: {minutes}分{seconds}秒",
                font=("Microsoft YaHei", 14),
                bg="#FFFFFF", fg="#888888").pack(pady=5)
        
        # 按钮区域
        btn_frame = tk.Frame(dialog, bg="#F5F5F5")
        btn_frame.pack(pady=20, fill=tk.X, padx=40)
        
        def on_restart():
            """再来一局 - 获取未学习的新单词"""
            print("[DEBUG] on_restart called")
            try:
                dialog.destroy()
            except Exception as e:
                print(f"[DEBUG] dialog.destroy error: {e}")
            # 延迟调用回调确保UI更新
            if self.next_round_callback:
                print(f"[DEBUG] Calling next_round_callback: {self.next_round_callback}")
                self.root.after(200, lambda: self.next_round_callback(result_data))
            elif self.on_game_over_callback:
                print(f"[DEBUG] Calling on_game_over_callback: {self.on_game_over_callback}")
                self.root.after(200, lambda: self.on_game_over_callback(result_data))
            else:
                print("[DEBUG] No callback available!")
        
        def on_exit():
            """退出 - 返回菜单"""
            try:
                dialog.destroy()
            except:
                pass
            if self.on_game_over_callback:
                self.root.after(200, lambda: self.on_game_over_callback(result_data))
        
        # 再来一局按钮 - 获取未学习的新单词
        tk.Button(btn_frame, text="🔄 再来一局",
                 font=("Microsoft YaHei", 14, "bold"),
                 bg="#4CAF50", fg="white",
                 relief=tk.RAISED, bd=3,
                 padx=20, pady=10,
                 command=on_restart).pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        
        # 退出按钮
        tk.Button(btn_frame, text="❌ 退出",
                 font=("Microsoft YaHei", 14, "bold"),
                 bg="#F44336", fg="white",
                 relief=tk.RAISED, bd=3,
                 padx=20, pady=10,
                 command=on_exit).pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
    
    def back_to_menu(self):
        """返回菜单"""
        self.game_running = False
        self.root.unbind('<Motion>')
        self.root.unbind('<Button-1>')
        
        if self.on_game_over_callback:
            self.on_game_over_callback(None)
