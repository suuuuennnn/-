"""
日历视图模块
显示学习打卡日历
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import calendar


class CalendarView:
    """学习日历视图"""
    
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db = db_manager
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        
    def show_calendar_window(self):
        """显示日历窗口"""
        win = tk.Toplevel(self.parent)
        win.title("📅 学习日历")
        win.geometry("900x700")
        win.configure(bg="#87CEEB")  # 天蓝色背景

        # 标题
        title_frame = tk.Frame(win, bg="#87CEEB")
        title_frame.pack(fill=tk.X, pady=12)

        tk.Button(title_frame, text="◀", font=("Microsoft YaHei", 18), width=3,
                 bg="#4CAF50", fg="white", command=self.prev_month).pack(side=tk.LEFT, padx=5)

        self.month_label = tk.Label(title_frame, text="",
                                   font=("Microsoft YaHei", 22, "bold"),
                                   bg="#87CEEB", fg="#2E8B57")
        self.month_label.pack(side=tk.LEFT, expand=True)

        tk.Button(title_frame, text="▶", font=("Microsoft YaHei", 18), width=3,
                 bg="#4CAF50", fg="white", command=self.next_month).pack(side=tk.RIGHT, padx=5)

        # 星期标题
        week_frame = tk.Frame(win, bg="#87CEEB")
        week_frame.pack(fill=tk.X, padx=20, pady=8)

        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        for i, day in enumerate(weekdays):
            label = tk.Label(week_frame, text=day, font=("Microsoft YaHei", 13, "bold"),
                           bg="#87CEEB", fg="#2E8B57", width=10)
            label.grid(row=0, column=i, padx=2, pady=2)

        # 日历网格
        self.calendar_frame = tk.Frame(win, bg="#87CEEB")
        self.calendar_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=12)

        # 统计信息
        self.stats_frame = tk.Frame(win, bg="#87CEEB")
        self.stats_frame.pack(fill=tk.X, padx=20, pady=12)

        # 关闭按钮
        tk.Button(win, text="关闭", font=("Microsoft YaHei", 13), bg="#F44336", fg="white",
                 command=win.destroy).pack(pady=12)

        # 渲染当前月份
        self.render_calendar()
    
    def render_calendar(self):
        """渲染日历"""
        # 清空旧内容
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        # 更新月份标签
        self.month_label.config(text=f"{self.current_year}年{self.current_month}月")
        
        # 获取当月数据
        checkins = self.db.get_monthly_checkins(self.current_year, self.current_month)
        checkin_dict = {c['date']: c for c in checkins}
        
        # 计算当月第一天是周几
        first_day = datetime(self.current_year, self.current_month, 1)
        first_weekday = first_day.weekday()  # 0=周一
        
        # 获取当月天数
        days_in_month = calendar.monthrange(self.current_year, self.current_month)[1]
        
        # 找到最高正确率
        max_accuracy = 0
        max_accuracy_date = None
        for date_str, checkin in checkin_dict.items():
            if checkin['accuracy'] > max_accuracy:
                max_accuracy = checkin['accuracy']
                max_accuracy_date = date_str
        
        # 创建日历格子
        row = 0
        col = first_weekday
        
        # 填充空白
        for i in range(first_weekday):
            empty = tk.Label(self.calendar_frame, text="", 
                           bg="#87CEEB", width=10, height=6)
            empty.grid(row=row, column=i, padx=2, pady=2)
        
        # 填充日期
        for day in range(1, days_in_month + 1):
            date_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
            checkin = checkin_dict.get(date_str)
            
            # 确定背景色和图标
            bg_color, icon = self._get_day_style(checkin, date_str, max_accuracy_date)
            
            # 创建日期框架
            day_frame = tk.Frame(self.calendar_frame, bg=bg_color, 
                               relief=tk.RAISED, bd=2)
            day_frame.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            
            # 配置网格权重
            self.calendar_frame.grid_rowconfigure(row, weight=1)
            self.calendar_frame.grid_columnconfigure(col, weight=1)
            
            # 日期数字
            date_label = tk.Label(day_frame, text=str(day),
                                font=("Microsoft YaHei", 11, "bold"),
                                bg=bg_color, anchor="nw")
            date_label.pack(fill=tk.X, padx=2, pady=2)

            # 图标
            if icon:
                icon_label = tk.Label(day_frame, text=icon,
                                    font=("Microsoft YaHei", 18),
                                    bg=bg_color)
                icon_label.pack(expand=True)

            # 正确率（如果有）
            if checkin:
                acc_label = tk.Label(day_frame,
                                   text=f"{checkin['accuracy']:.0f}%",
                                   font=("Microsoft YaHei", 9),
                                   bg=bg_color)
                acc_label.pack(fill=tk.X, padx=2, pady=2)
            
            col += 1
            if col > 6:
                col = 0
                row += 1
        
        # 显示统计信息
        self._show_month_stats(checkin_dict, max_accuracy, max_accuracy_date)
    
    def _get_day_style(self, checkin, date_str, max_accuracy_date):
        """
        根据学习情况获取日期的样式
        
        Returns:
            tuple: (背景色, 图标)
        """
        if not checkin:
            return "#D3D3D3", ""  # 灰色 - 无学习
        
        # 有学习记录，显示绿色
        total = checkin['new_words_count'] + checkin['review_words_count']
        
        if total == 0:
            return "#D3D3D3", ""  # 灰色 - 无学习
        
        # 计算完成度
        plan_target = 10  # 默认每日目标
        completion_rate = total / plan_target if plan_target > 0 else 0
        
        if completion_rate > 1.0:
            return "#4CAF50", "🌟"  # 绿色+星星 - 超额完成
        elif completion_rate >= 0.5:
            return "#81C784", "✅"  # 浅绿色+勾 - 完成良好
        else:
            return "#A5D6A7", "📚"  # 更浅的绿色+书 - 已学习
    
    def _show_month_stats(self, checkin_dict, max_accuracy, max_accuracy_date):
        """显示月度统计信息"""
        # 清空统计框架
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        total_days = len(checkin_dict)
        if total_days == 0:
            tk.Label(self.stats_frame, text="本月暂无学习记录",
                    font=("Microsoft YaHei", 15), bg="#87CEEB", fg="#2E8B57").pack()
            return

        # 计算平均正确率
        total_accuracy = sum(c['accuracy'] for c in checkin_dict.values())
        avg_accuracy = total_accuracy / total_days

        stats_text = f"本月学习天数: {total_days}天 | "
        stats_text += f"平均正确率: {avg_accuracy:.1f}% | "

        if max_accuracy_date:
            date_obj = datetime.strptime(max_accuracy_date, "%Y-%m-%d")
            stats_text += f"最佳正确率: {max_accuracy:.0f}% ({date_obj.month}月{date_obj.day}日) 👑"

        tk.Label(self.stats_frame, text=stats_text,
                font=("Microsoft YaHei", 13), bg="#87CEEB", fg="#2E8B57").pack()
    
    def prev_month(self):
        """上一个月"""
        if self.current_month == 1:
            self.current_year -= 1
            self.current_month = 12
        else:
            self.current_month -= 1
        self.render_calendar()
    
    def next_month(self):
        """下一个月"""
        if self.current_month == 12:
            self.current_year += 1
            self.current_month = 1
        else:
            self.current_month += 1
        self.render_calendar()
