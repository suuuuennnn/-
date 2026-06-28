import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import random
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
from PIL import Image, ImageTk, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import winsound

# ----------------------------- 1. 学习数据管理模块 -----------------------------
class LearningDataManager:
    def __init__(self):
        self.data_file = "learning_data.json"
        self.wrong_words_file = "wrong_words.json"
        self.learning_records = []
        self.wrong_words = {}
        self.load_data()
        self.load_wrong_words()

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.learning_records = data.get("records", [])
        except:
            self.learning_records = []

    def save_data(self):
        try:
            data = {"records": self.learning_records}
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def load_wrong_words(self):
        try:
            if os.path.exists(self.wrong_words_file):
                with open(self.wrong_words_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.wrong_words = data.get("wrong_words", {})
        except:
            self.wrong_words = {}

    def save_wrong_words(self):
        try:
            data = {"wrong_words": self.wrong_words}
            with open(self.wrong_words_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def record_learning_session(self, total_questions, correct_count, words_learned):
        record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": total_questions,
            "correct": correct_count,
            "accuracy": (correct_count / total_questions * 100) if total_questions > 0 else 0,
            "words_count": len(words_learned)
        }
        self.learning_records.append(record)
        self.save_data()

    def add_wrong_word(self, word_data):
        eng = word_data.get("eng", "")
        if eng:
            if eng not in self.wrong_words:
                self.wrong_words[eng] = {
                    "count": 0,
                    "last_error_time": "",
                    "word_data": word_data
                }
            self.wrong_words[eng]["count"] += 1
            self.wrong_words[eng]["last_error_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.wrong_words[eng]["word_data"] = word_data
            self.save_wrong_words()

    def get_sorted_wrong_words(self):
        return sorted(self.wrong_words.items(), key=lambda x: x[1]["count"], reverse=True)

    def clear_wrong_words(self):
        self.wrong_words = {}
        self.save_wrong_words()

    def get_heatmap_data(self, year=None, month=None):
        heatmap_data = defaultdict(int)
        for record in self.learning_records:
            try:
                date_str = record["date"][:10]
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                if year and date_obj.year != year:
                    continue
                if month and date_obj.month != month:
                    continue
                heatmap_data[date_str] += 1
            except:
                continue
        return dict(heatmap_data)

    def get_accuracy_trend(self, days=30):
        trend_data = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        for record in self.learning_records:
            try:
                date_str = record["date"][:10]
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                if start_date <= date_obj <= end_date:
                    trend_data.append({"date": date_str, "accuracy": record["accuracy"]})
            except:
                continue
        return trend_data

# ----------------------------- 2. 音效管理模块 -----------------------------
class SoundManager:
    def __init__(self):
        self.sound_enabled = True
        self.sound_configs = {
            "correct": (800, 150),
            "wrong": (300, 300),
            "combo": (1200, 200),
            "game_over": (500, 500)
        }

    def play_sound(self, sound_type):
        if not self.sound_enabled:
            return
        try:
            freq, duration = self.sound_configs.get(sound_type, (600, 200))
            winsound.Beep(freq, duration)
        except:
            pass

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        return self.sound_enabled

# ----------------------------- 3. 单词管理模块 -----------------------------
class WordManager:
    def __init__(self):
        self.all_words = []
        self.today_words = []
        self.settings_file = "settings.json"
        self.load_settings()

    def load_words_from_file(self, filename):
        words = []
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    if ',' in line:
                        parts = line.split(",")
                    elif '\t' in line:
                        parts = line.split("\t")
                    else:
                        parts = line.split()
                    if len(parts) >= 2:
                        eng = parts[0].strip()
                        meanings = [m.strip() for m in parts[1:] if m.strip()]
                        if eng and meanings:
                            words.append({"eng": eng, "meanings": meanings})
                    if line_num % 1000 == 0:
                        print(f"已加载 {line_num} 行...")
            return words
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败：{str(e)}")
            return []

    def select_today_words(self, count):
        if len(self.all_words) < count:
            count = len(self.all_words)
        self.today_words = random.sample(self.all_words, count)
        self.save_settings()
        return self.today_words

    def save_settings(self):
        settings = {"total_words": len(self.all_words), "last_words": self.today_words[:100] if self.today_words else []}
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except:
            pass

    def load_settings(self):
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

# ----------------------------- 4. 图表生成模块 -----------------------------
class ChartGenerator:
    @staticmethod
    def generate_heatmap(heatmap_data, year, month, save_path="heatmap.png"):
        try:
            import calendar
            first_day = datetime(year, month, 1)
            if month == 12:
                last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(year, month + 1, 1) - timedelta(days=1)
            days_in_month = (last_day - first_day).days + 1
            dates = [first_day + timedelta(days=i) for i in range(days_in_month)]
            values = [heatmap_data.get(date.strftime("%Y-%m-%d"), 0) for date in dates]

            weeks = (days_in_month + first_day.weekday()) // 7 + 1
            heatmap_array = [[0] * weeks for _ in range(7)]
            for i, (date, value) in enumerate(zip(dates, values)):
                week_idx = (first_day.weekday() + i) // 7
                day_idx = (first_day.weekday() + i) % 7
                heatmap_array[day_idx][week_idx] = value

            fig, ax = plt.subplots(figsize=(12, 6))
            im = ax.imshow(heatmap_array, cmap='YlOrRd', aspect='auto')
            day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            ax.set_yticks(range(7))
            ax.set_yticklabels(day_names)
            ax.set_xticks(range(weeks))
            ax.set_xticklabels([f'第{i+1}周' for i in range(weeks)])
            ax.set_title(f'{year}年{month}月 学习热力图', fontsize=16, fontweight='bold')
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('学习次数', rotation=270, labelpad=20)
            for i in range(7):
                for j in range(weeks):
                    if heatmap_array[i][j] > 0:
                        ax.text(j, i, str(heatmap_array[i][j]), ha="center", va="center", color="black", fontsize=8)
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return True
        except Exception as e:
            print(f"生成热力图失败: {e}")
            return False

    @staticmethod
    def generate_accuracy_trend(trend_data, save_path="accuracy_trend.png"):
        try:
            dates = [datetime.strptime(item["date"], "%Y-%m-%d") for item in trend_data]
            accuracies = [item["accuracy"] for item in trend_data]
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(dates, accuracies, marker='o', linewidth=2, markersize=6, color='#2E8B57', label='正确率')
            ax.fill_between(dates, accuracies, alpha=0.3, color='#2E8B57')
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('正确率 (%)', fontsize=12)
            ax.set_title('正确率趋势图', fontsize=16, fontweight='bold')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
            plt.xticks(rotation=45)
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.legend(loc='best')
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            return True
        except Exception as e:
            print(f"生成趋势图失败: {e}")
            return False

# ----------------------------- 5. 打地鼠游戏主类 -----------------------------
class WhackGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🐭 专业版单词打地鼠")
        self.root.geometry("1000x700")
        self.root.configure(bg="#2E8B57")

        self.word_manager = WordManager()
        self.data_manager = LearningDataManager()
        self.sound_manager = SoundManager()
        self.game_running = False
        self.score = 0
        self.total_questions = 0
        self.current_question = 0
        self.mode = None
        self.current_word = None
        self.correct_option_index = None
        self.combo_count = 0
        self.combo_bonus = 0

        self.load_images()
        self.create_main_menu()

    # ----------------------------- 图片加载与绘制 -----------------------------
    def create_default_image(self, color, emoji, size=80):
        """创建带圆形背景和 emoji 的图片"""
        img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        margin = 5
        draw.ellipse([margin, margin, size-margin, size-margin], fill=color)
        try:
            # 尝试使用 emoji 字体
            font = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", size // 2)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size // 2)
            except:
                font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), emoji, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2 - bbox[0]
        y = (size - text_height) // 2 - bbox[1]
        draw.text((x, y), emoji, font=font, fill="white")
        return ImageTk.PhotoImage(img)

    def load_images(self):
        """加载图片资源，支持外部图片"""
        self.mouse_img = self.create_default_image("#8B6914", "🐭", 80)
        self.hammer_img = self.create_default_image("#FF6347", "🔨", 40)   # 锤子小一些
        self.runaway_img = self.create_default_image("#D2B48C", "💨", 80)
        self.injured_img = self.create_default_image("#CD5C5C", "😵", 80)
        self.load_external_images()

    def load_external_images(self):
        """加载外部图片，如果存在则覆盖默认"""
        image_files = {
            "mouse": ["mouse.png", "mouse.gif", "mole.png", "地鼠.png"],
            "hammer": ["hammer.png", "hit.png", "锤子.png"],
            "runaway": ["runaway.png", "escape.png", "逃跑.png"],
            "injured": ["injured.png", "hurt.png", "受伤.png"]
        }
        sizes = {"mouse": 80, "hammer": 40, "runaway": 80, "injured": 80}
        for key, filenames in image_files.items():
            for filename in filenames:
                if os.path.exists(filename):
                    try:
                        img = Image.open(filename)
                        size = sizes.get(key, 80)
                        img = img.resize((size, size), Image.Resampling.LANCZOS)
                        setattr(self, f"{key}_img", ImageTk.PhotoImage(img))
                        print(f"成功加载图片: {filename} ({size}x{size})")
                        break
                    except Exception as e:
                        print(f"加载图片失败 {filename}: {e}")

    # ----------------------------- 主菜单界面 -----------------------------
    def create_main_menu(self):
        self.clear_window()
        title = tk.Label(self.root, text="🐭 单词打地鼠游戏 🐭", font=("Arial", 36, "bold"),
                         bg="#2E8B57", fg="#FFD700")
        title.pack(pady=20)

        tk.Button(self.root, text=f"🔊 音效: {'开' if self.sound_manager.sound_enabled else '关'}",
                  font=("Arial", 12), bg="#FF9800", fg="white", command=self.toggle_sound).pack(pady=5)

        import_frame = tk.Frame(self.root, bg="#2E8B57")
        import_frame.pack(pady=10)
        tk.Label(import_frame, text="单词文件：", font=("Arial", 14), bg="#2E8B57", fg="white").pack(side=tk.LEFT, padx=10)
        self.file_label = tk.Label(import_frame, text="未选择文件", font=("Arial", 12), bg="#2E8B57", fg="#FFD700")
        self.file_label.pack(side=tk.LEFT, padx=10)
        tk.Button(import_frame, text="📁 导入单词本", font=("Arial", 12), bg="#4CAF50", fg="white", command=self.import_words).pack(side=tk.LEFT, padx=10)

        self.stats_label = tk.Label(self.root, text="", bg="#2E8B57", fg="white")
        self.stats_label.pack(pady=5)

        count_frame = tk.Frame(self.root, bg="#2E8B57")
        count_frame.pack(pady=10)
        tk.Label(count_frame, text="今日学习数量：", font=("Arial", 14), bg="#2E8B57", fg="white").pack(side=tk.LEFT, padx=10)
        self.count_var = tk.IntVar(value=10)
        tk.Spinbox(count_frame, from_=5, to=100, width=10, font=("Arial", 12), textvariable=self.count_var).pack(side=tk.LEFT, padx=10)

        mode_frame = tk.Frame(self.root, bg="#2E8B57")
        mode_frame.pack(pady=10)
        tk.Label(mode_frame, text="选择模式：", font=("Arial", 14), bg="#2E8B57", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(mode_frame, text="英 → 中", font=("Arial", 14), width=10, bg="#FF9800", fg="white",
                  command=lambda: self.start_game("eng2chn")).pack(side=tk.LEFT, padx=10)
        tk.Button(mode_frame, text="中 → 英", font=("Arial", 14), width=10, bg="#FF9800", fg="white",
                  command=lambda: self.start_game("chn2eng")).pack(side=tk.LEFT, padx=10)

        func_frame1 = tk.Frame(self.root, bg="#2E8B57")
        func_frame1.pack(pady=10)
        tk.Button(func_frame1, text="📊 学习热力图", font=("Arial", 12), width=12, bg="#2196F3", fg="white", command=self.show_heatmap).pack(side=tk.LEFT, padx=10)
        tk.Button(func_frame1, text="📈 正确率趋势", font=("Arial", 12), width=12, bg="#2196F3", fg="white", command=self.show_accuracy_trend).pack(side=tk.LEFT, padx=10)

        func_frame2 = tk.Frame(self.root, bg="#2E8B57")
        func_frame2.pack(pady=10)
        tk.Button(func_frame2, text="❌ 错词本", font=("Arial", 12), width=12, bg="#F44336", fg="white", command=self.show_wrong_words).pack(side=tk.LEFT, padx=10)
        tk.Button(func_frame2, text="🔄 复习错词", font=("Arial", 12), width=12, bg="#FF5722", fg="white", command=self.review_wrong_words).pack(side=tk.LEFT, padx=10)

        tk.Button(self.root, text="🖼️ 更换图片", font=("Arial", 12), bg="#9C27B0", fg="white", command=self.change_mouse_image).pack(pady=5)

    def toggle_sound(self):
        enabled = self.sound_manager.toggle_sound()
        messagebox.showinfo("音效设置", f"音效已{'开' if enabled else '关'}")
        self.create_main_menu()

    def import_words(self):
        filename = filedialog.askopenfilename(title="选择单词本", filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv")])
        if filename:
            words = self.word_manager.load_words_from_file(filename)
            if words:
                self.word_manager.all_words = words
                self.file_label.config(text=os.path.basename(filename))
                self.stats_label.config(text=f"✅ 已加载 {len(words)} 个单词")
                messagebox.showinfo("成功", f"成功导入 {len(words)} 个单词！")

    # ----------------------------- 游戏核心逻辑 -----------------------------
    def start_game(self, mode):
        if not self.word_manager.all_words:
            messagebox.showwarning("警告", "请先导入单词本！")
            return
        count = self.count_var.get()
        self.word_manager.select_today_words(count)
        if not self.word_manager.today_words:
            messagebox.showwarning("警告", "没有足够的单词！")
            return
        self.mode = mode
        self.score = 0
        self.total_questions = min(20, len(self.word_manager.today_words) * 2)
        self.current_question = 0
        self.game_running = True
        self.combo_count = 0
        self.combo_bonus = 0
        self.create_game_ui()
        self.next_question()

    def create_game_ui(self):
        self.clear_window()
        info_frame = tk.Frame(self.root, bg="#2E8B57")
        info_frame.pack(fill=tk.X, pady=10)
        self.score_label = tk.Label(info_frame, text=f"得分: {self.score}", font=("Arial", 18, "bold"), bg="#2E8B57", fg="#FFD700")
        self.score_label.pack(side=tk.LEFT, padx=20)
        self.combo_label = tk.Label(info_frame, text="", font=("Arial", 16, "bold"), bg="#2E8B57", fg="#FF6347")
        self.combo_label.pack(side=tk.LEFT, padx=20)
        self.progress_label = tk.Label(info_frame, text=f"进度: 0/{self.total_questions}", font=("Arial", 18), bg="#2E8B57", fg="white")
        self.progress_label.pack(side=tk.RIGHT, padx=20)

        self.question_label = tk.Label(self.root, text="", font=("Arial", 32, "bold"), bg="#2E8B57", fg="white")
        self.question_label.pack(pady=30)

        self.mice_frame = tk.Frame(self.root, bg="#2E8B57")
        self.mice_frame.pack(expand=True)
        self.mice_buttons = []
        for i in range(4):
            btn = tk.Button(self.mice_frame, image=self.mouse_img, text="", compound="top",
                            font=("Arial", 11, "bold"), width=130, height=130,
                            bg="#8B4513", activebackground="#A0522D", relief=tk.RAISED, bd=4,
                            wraplength=110, command=lambda idx=i: self.check_answer(idx))
            btn.grid(row=i//2, column=i%2, padx=25, pady=25)
            self.mice_buttons.append(btn)

        # 锤子标签（跟随鼠标）
        self.hammer_label = tk.Label(self.root, image=self.hammer_img, bg="#2E8B57")
        self.hammer_label.place(x=-100, y=-100)
        self.root.bind('<Motion>', self.move_hammer)
        self.root.bind('<Button-1>', self.on_click)

        tk.Button(self.root, text="返回菜单", font=("Arial", 12), bg="#F44336", fg="white", command=self.back_to_menu).pack(pady=20)

    def move_hammer(self, event):
        """锤子中心对准鼠标位置"""
        if self.game_running:
            # 获取锤子图片的实际尺寸（宽度、高度）
            w = self.hammer_img.width() if hasattr(self.hammer_img, 'width') else 40
            h = self.hammer_img.height() if hasattr(self.hammer_img, 'height') else 40
            # 让锤子标签的左上角坐标 = 鼠标坐标 - 锤子一半尺寸
            x = event.x - w // 2
            y = event.y - h // 2
            self.hammer_label.place(x=x, y=y)

    def on_click(self, event):
        if not self.game_running:
            return
        x, y = self.hammer_label.winfo_x(), self.hammer_label.winfo_y()
        # 敲击动画：向下移动 15 像素后恢复
        self.hammer_label.place(x=x, y=y+15)
        self.root.after(50, lambda: self.hammer_label.place(x=x, y=y))

    def next_question(self):
        if self.current_question >= self.total_questions:
            self.game_over()
            return
        self.current_question += 1
        self.update_progress()
        self.current_word = random.choice(self.word_manager.today_words)
        if self.mode == "eng2chn":
            question_text = f"🐭 {self.current_word['eng']} 的中文意思是？"
            correct_option = random.choice(self.current_word["meanings"])
            options = self.generate_options(correct_option, is_english=False)
            self.correct_option_index = options.index(correct_option)
            for i, btn in enumerate(self.mice_buttons):
                btn.config(text=options[i], image=self.mouse_img, compound="top", state=tk.NORMAL, bg="#8B4513", relief=tk.RAISED)
        else:
            current_chinese = random.choice(self.current_word["meanings"])
            question_text = f"🐭 “{current_chinese}” 的英文是？"
            correct_option = self.current_word["eng"]
            options = self.generate_options(correct_option, is_english=True)
            self.correct_option_index = options.index(correct_option)
            for i, btn in enumerate(self.mice_buttons):
                btn.config(text=options[i], image=self.mouse_img, compound="top", state=tk.NORMAL, bg="#8B4513", relief=tk.RAISED)
        self.question_label.config(text=question_text)

    def generate_options(self, correct_option, is_english=False):
        options = [correct_option]
        candidates = []
        if is_english:
            for w in self.word_manager.today_words:
                if w["eng"] != correct_option:
                    candidates.append(w["eng"])
        else:
            for w in self.word_manager.today_words:
                for meaning in w["meanings"]:
                    if meaning != correct_option:
                        candidates.append(meaning)
        candidates = list(set(candidates))
        random.shuffle(candidates)
        for cand in candidates:
            if len(options) >= 4:
                break
            if cand not in options:
                options.append(cand)
        while len(options) < 4:
            options.append("???")
        random.shuffle(options)
        return options

    def check_answer(self, idx):
        if not self.game_running:
            return
        for btn in self.mice_buttons:
            btn.config(state=tk.DISABLED)
        if idx == self.correct_option_index:
            self.combo_count += 1
            self.combo_bonus = (self.combo_count // 5) * 5
            total_score = 10 + self.combo_bonus
            self.score += total_score
            self.update_score()
            self.update_combo_display()
            self.sound_manager.play_sound("correct")
            if self.combo_count > 0 and self.combo_count % 5 == 0:
                self.sound_manager.play_sound("combo")
            self.play_hit_animation(idx, True)
        else:
            self.combo_count = 0
            self.combo_bonus = 0
            self.score = max(0, self.score - 5)
            self.update_score()
            self.update_combo_display()
            if self.current_word:
                self.data_manager.add_wrong_word(self.current_word)
            self.sound_manager.play_sound("wrong")
            self.play_hit_animation(idx, False)

    def play_hit_animation(self, button_idx, is_correct):
        if is_correct:
            correct_btn = self.mice_buttons[button_idx]
            correct_btn.config(image=self.injured_img, bg="#CD5C5C", relief=tk.SUNKEN)
            self.root.after(500, lambda: self.reset_after_correct(button_idx))
        else:
            for btn in self.mice_buttons:
                btn.config(image=self.runaway_img, bg="#D2B48C", relief=tk.FLAT)
            self.root.after(600, self.reset_after_wrong)

    def reset_after_correct(self, button_idx):
        self.mice_buttons[button_idx].config(image=self.mouse_img, bg="#8B4513", relief=tk.RAISED)
        self.next_question()

    def reset_after_wrong(self):
        for btn in self.mice_buttons:
            btn.config(image=self.mouse_img, bg="#8B4513", relief=tk.RAISED)
        self.next_question()

    def update_score(self):
        self.score_label.config(text=f"得分: {self.score}")

    def update_combo_display(self):
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
        self.progress_label.config(text=f"进度: {self.current_question}/{self.total_questions}")

    def game_over(self):
        self.game_running = False
        correct_count = self.score // 10
        self.data_manager.record_learning_session(self.total_questions, correct_count, self.word_manager.today_words)
        self.sound_manager.play_sound("game_over")
        accuracy = (self.score / (self.total_questions * 10)) * 100 if self.total_questions > 0 else 0
        result = f"游戏结束！\n\n得分: {self.score}\n正确率: {accuracy:.1f}%\n"
        if accuracy >= 80:
            result += "\n🎉 太棒了！单词大师！"
        elif accuracy >= 60:
            result += "\n👍 不错，继续努力！"
        else:
            result += "\n📚 多练习几次会更好！"
        messagebox.showinfo("游戏结束", result)
        self.back_to_menu()

    # ----------------------------- 统计与错词本界面 -----------------------------
    def show_heatmap(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("选择月份")
        dialog.geometry("300x200")
        dialog.configure(bg="#2E8B57")
        tk.Label(dialog, text="选择年份：", font=("Arial", 12), bg="#2E8B57", fg="white").pack(pady=10)
        year_var = tk.IntVar(value=datetime.now().year)
        tk.Spinbox(dialog, from_=2020, to=2030, width=10, font=("Arial", 12), textvariable=year_var).pack(pady=5)
        tk.Label(dialog, text="选择月份：", font=("Arial", 12), bg="#2E8B57", fg="white").pack(pady=10)
        month_var = tk.IntVar(value=datetime.now().month)
        tk.Spinbox(dialog, from_=1, to=12, width=10, font=("Arial", 12), textvariable=month_var).pack(pady=5)

        def generate():
            year, month = year_var.get(), month_var.get()
            data = self.data_manager.get_heatmap_data(year, month)
            if not data:
                messagebox.showinfo("提示", "该月没有学习记录")
                dialog.destroy()
                return
            path = f"heatmap_{year}_{month}.png"
            if ChartGenerator.generate_heatmap(data, year, month, path):
                dialog.destroy()
                self.show_chart_in_window(path, f"{year}年{month}月 学习热力图")
            else:
                messagebox.showerror("错误", "生成热力图失败")
                dialog.destroy()
        tk.Button(dialog, text="生成热力图", font=("Arial", 12), bg="#4CAF50", fg="white", command=generate).pack(pady=20)

    def show_accuracy_trend(self):
        data = self.data_manager.get_accuracy_trend(days=30)
        if not data:
            messagebox.showinfo("提示", "没有足够的学习数据")
            return
        path = "accuracy_trend.png"
        if ChartGenerator.generate_accuracy_trend(data, path):
            self.show_chart_in_window(path, "正确率趋势图")
        else:
            messagebox.showerror("错误", "生成趋势图失败")

    def show_chart_in_window(self, image_path, title):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("900x700")
        win.configure(bg="#f0f0f0")
        tk.Label(win, text=title, font=("Arial", 18, "bold"), bg="#f0f0f0", fg="#2E8B57").pack(pady=10)
        try:
            img = Image.open(image_path)
            img = img.resize((850, 600), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(win, image=photo, bg="#f0f0f0")
            label.image = photo
            label.pack(pady=10)
        except Exception as e:
            tk.Label(win, text=f"图片加载失败：{str(e)}", font=("Arial", 12), bg="#f0f0f0", fg="red").pack(pady=20)
        btn_frame = tk.Frame(win, bg="#f0f0f0")
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="📁 打开文件位置", font=("Arial", 12), bg="#2196F3", fg="white",
                  command=lambda: self.open_file_location(image_path)).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="关闭", font=("Arial", 12), bg="#4CAF50", fg="white", command=win.destroy).pack(side=tk.LEFT, padx=10)

    def open_file_location(self, file_path):
        import subprocess, platform
        abs_path = os.path.abspath(file_path)
        try:
            if platform.system() == "Windows":
                os.startfile(os.path.dirname(abs_path))
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", os.path.dirname(abs_path)])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(abs_path)])
        except:
            messagebox.showerror("错误", "无法打开文件夹")

    def show_wrong_words(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("❌ 错词本")
        dialog.geometry("800x600")
        dialog.configure(bg="#2E8B57")
        tk.Label(dialog, text="错词本", font=("Arial", 24, "bold"), bg="#2E8B57", fg="#FFD700").pack(pady=10)
        wrong_list = self.data_manager.get_sorted_wrong_words()
        tk.Label(dialog, text=f"共有 {len(wrong_list)} 个错词", font=("Arial", 14), bg="#2E8B57", fg="white").pack(pady=5)
        canvas = tk.Canvas(dialog, bg="#2E8B57")
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#2E8B57")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        if wrong_list:
            for idx, (word, info) in enumerate(wrong_list):
                frame = tk.Frame(scroll_frame, bg="#3E8B57", relief=tk.RAISED, bd=2)
                frame.pack(fill=tk.X, padx=10, pady=5)
                tk.Label(frame, text=f"{idx+1}. {word} - 错误次数: {info['count']}", font=("Arial", 14, "bold"),
                         bg="#3E8B57", fg="#FFD700", anchor="w").pack(fill=tk.X, padx=10, pady=5)
                meanings = "; ".join(info["word_data"].get("meanings", []))
                tk.Label(frame, text=f"释义: {meanings}", font=("Arial", 12), bg="#3E8B57", fg="white",
                         anchor="w", wraplength=700).pack(fill=tk.X, padx=10, pady=2)
                tk.Label(frame, text=f"最后错误: {info['last_error_time']}", font=("Arial", 10),
                         bg="#3E8B57", fg="#CCCCCC", anchor="w").pack(fill=tk.X, padx=10, pady=2)
        else:
            tk.Label(scroll_frame, text="暂无错词，继续加油！", font=("Arial", 16), bg="#2E8B57", fg="white").pack(pady=50)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        btn_frame = tk.Frame(dialog, bg="#2E8B57")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="🗑️ 清空错词本", font=("Arial", 12), bg="#F44336", fg="white",
                  command=lambda: self.clear_wrong_words(dialog)).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="关闭", font=("Arial", 12), bg="#9E9E9E", fg="white", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

    def clear_wrong_words(self, dialog):
        if messagebox.askyesno("确认", "确定要清空错词本吗？"):
            self.data_manager.clear_wrong_words()
            messagebox.showinfo("成功", "错词本已清空")
            dialog.destroy()
            self.show_wrong_words()

    def review_wrong_words(self):
        wrong_list = self.data_manager.get_sorted_wrong_words()
        if not wrong_list:
            messagebox.showinfo("提示", "错词本为空，无需复习")
            return
        review_words = [info["word_data"] for _, info in wrong_list[:20]]
        self.word_manager.today_words = review_words
        self.mode = "eng2chn"
        self.score = 0
        self.total_questions = min(20, len(review_words))
        self.current_question = 0
        self.game_running = True
        self.combo_count = 0
        self.combo_bonus = 0
        self.create_game_ui()
        self.next_question()

    # ----------------------------- 更换图片功能 -----------------------------
    def change_mouse_image(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("🖼️ 更换游戏图片")
        dialog.geometry("400x350")
        dialog.configure(bg="#2E8B57")
        tk.Label(dialog, text="选择要更换的图片", font=("Arial", 18, "bold"), bg="#2E8B57", fg="#FFD700").pack(pady=15)
        tk.Label(dialog, text="可以为游戏中的不同效果更换图片", font=("Arial", 10), bg="#2E8B57", fg="white").pack(pady=5)
        btn_frame = tk.Frame(dialog, bg="#2E8B57")
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="🐭 更换地鼠图片", font=("Arial", 12), width=18, bg="#8B6914", fg="white",
                  command=lambda: self.select_and_change_image("mouse", dialog)).pack(pady=8)
        tk.Button(btn_frame, text="🔨 更换锤子图片", font=("Arial", 12), width=18, bg="#FF6347", fg="white",
                  command=lambda: self.select_and_change_image("hammer", dialog)).pack(pady=8)
        tk.Button(btn_frame, text="💨 更换逃跑图片", font=("Arial", 12), width=18, bg="#D2B48C", fg="black",
                  command=lambda: self.select_and_change_image("runaway", dialog)).pack(pady=8)
        tk.Button(btn_frame, text="😵 更换受伤图片", font=("Arial", 12), width=18, bg="#CD5C5C", fg="white",
                  command=lambda: self.select_and_change_image("injured", dialog)).pack(pady=8)
        tk.Button(dialog, text="关闭", font=("Arial", 12), bg="#9E9E9E", fg="white", command=dialog.destroy).pack(pady=10)

    def select_and_change_image(self, image_type, dialog=None):
        filename = filedialog.askopenfilename(title=f"选择{image_type}图片",
                                              filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if filename:
            try:
                size = 80 if image_type != "hammer" else 40
                img = Image.open(filename)
                img = img.resize((size, size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                setattr(self, f"{image_type}_img", photo)
                if self.game_running:
                    if image_type == "mouse" and hasattr(self, 'mice_buttons'):
                        for btn in self.mice_buttons:
                            btn.config(image=self.mouse_img)
                    elif image_type == "hammer" and hasattr(self, 'hammer_label'):
                        self.hammer_label.config(image=self.hammer_img)
                type_names = {"mouse": "地鼠", "hammer": "锤子", "runaway": "逃跑", "injured": "受伤"}
                messagebox.showinfo("成功", f"{type_names[image_type]}图片已更换！\n立即生效")
                if dialog:
                    dialog.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"图片加载失败：{str(e)}")

    # ----------------------------- 辅助方法 -----------------------------
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def back_to_menu(self):
        self.game_running = False
        self.create_main_menu()

# ----------------------------- 启动 -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    game = WhackGame(root)
    root.mainloop()