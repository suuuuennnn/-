"""
统计图表模块
使用matplotlib生成各种学习统计图表
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class StatisticsGenerator:
    """统计图表生成器"""
    
    @staticmethod
    def generate_accuracy_trend(daily_stats, save_path="accuracy_trend.png"):
        """
        生成正确率趋势图
        
        Args:
            daily_stats: 每日统计数据列表
            save_path: 保存路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 准备数据
            dates = []
            accuracies = []
            
            if daily_stats:
                for stat in reversed(daily_stats):  # 反转使日期从早到晚
                    try:
                        date_obj = datetime.strptime(stat['date'], "%Y-%m-%d")
                        dates.append(date_obj)
                        accuracies.append(stat.get('accuracy', 0))
                    except:
                        continue
            
            # 创建图表
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if dates:
                ax.plot(dates, accuracies, marker='o', linewidth=2, markersize=6, 
                       color='#2E8B57', label='正确率')
                ax.fill_between(dates, accuracies, alpha=0.3, color='#2E8B57')
                ax.set_title('近30天正确率趋势', fontsize=16, fontweight='bold')
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
                ax.legend(loc='best')
                ax.set_ylim(0, 100)  # 正确率 0-100%
            else:
                # 无数据时显示占位符
                ax.text(0.5, 0.5, '暂无学习数据\n开始学习后将会显示趋势图', 
                       ha='center', va='center', fontsize=16, 
                       transform=ax.transAxes, color='#999999')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_xticks([])
                ax.set_yticks([])
            
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('正确率 (%)', fontsize=12)
            plt.xticks(rotation=45)
            ax.grid(True, linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True
        except Exception as e:
            print(f"生成趋势图失败: {e}")
            return False
    
    @staticmethod
    def generate_mastery_pie(mastery_data, save_path="mastery_pie.png"):
        """
        生成掌握进度饼图
        
        Args:
            mastery_data: {'mastered': n, 'learning': n, 'not_started': n}
            save_path: 保存路径
            
        Returns:
            bool: 是否成功
        """
        try:
            labels = ['已掌握', '学习中', '未开始']
            sizes = [
                mastery_data.get('mastered', 0),
                mastery_data.get('learning', 0),
                mastery_data.get('not_started', 0)
            ]
            
            if sum(sizes) == 0:
                return False
            
            colors = ['#4CAF50', '#FF9800', '#9E9E9E']
            explode = (0.05, 0.05, 0.05)
            
            fig, ax = plt.subplots(figsize=(8, 8))
            wedges, texts, autotexts = ax.pie(
                sizes, 
                explode=explode, 
                labels=labels, 
                colors=colors,
                autopct='%1.1f%%',
                shadow=True,
                startangle=90
            )
            
            for autotext in autotexts:
                autotext.set_fontsize(12)
                autotext.set_fontweight('bold')
            
            ax.set_title('单词掌握进度', fontsize=16, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True
        except Exception as e:
            print(f"生成饼图失败: {e}")
            return False
    
    @staticmethod
    def generate_wrong_words_trend(wrong_words_history, save_path="wrong_words_trend.png"):
        """
        生成错词下降曲线
        
        Args:
            wrong_words_history: [(date, count), ...]
            save_path: 保存路径
            
        Returns:
            bool: 是否成功
        """
        try:
            dates = []
            counts = []
            
            for date_str, count in wrong_words_history:
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    dates.append(date_obj)
                    counts.append(count)
                except:
                    continue
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if dates:
                ax.plot(dates, counts, marker='s', linewidth=2, markersize=6,
                       color='#F44336', label='错词数量')
                ax.fill_between(dates, counts, alpha=0.3, color='#F44336')
                ax.set_title('错词数量变化趋势', fontsize=16, fontweight='bold')
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
                ax.legend(loc='best')
            else:
                # 无数据时显示占位符
                ax.text(0.5, 0.5, '暂无错词数据\n开始学习后将会显示错词趋势', 
                       ha='center', va='center', fontsize=16, 
                       transform=ax.transAxes, color='#999999')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_xticks([])
                ax.set_yticks([])
            
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('错词数量', fontsize=12)
            plt.xticks(rotation=45)
            ax.grid(True, linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True
        except Exception as e:
            print(f"生成错词趋势图失败: {e}")
            return False
    
    @staticmethod
    def generate_study_duration_chart(daily_stats, days=7, save_path="study_duration.png"):
        """
        生成学习时长分布图
        
        Args:
            daily_stats: 每日统计数据列表
            days: 天数（7或30）
            save_path: 保存路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 取最近N天
            recent_stats = daily_stats[:days] if daily_stats else []
            
            dates = []
            durations = []
            
            for stat in reversed(recent_stats):
                try:
                    date_obj = datetime.strptime(stat['date'], "%Y-%m-%d")
                    dates.append(date_obj.strftime('%m-%d'))
                    durations.append(stat.get('duration_seconds', 0) / 60)  # 转换为分钟
                except:
                    continue
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if dates:
                bars = ax.bar(dates, durations, color='#2196F3', alpha=0.7, edgecolor='black')
                
                # 在柱状图上添加数值标签
                for bar, duration in zip(bars, durations):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{duration:.1f}分',
                           ha='center', va='bottom', fontsize=9)
                ax.set_title(f'近{days}天学习时长分布', fontsize=16, fontweight='bold')
                ax.set_ylim(0, 120)  # 2小时 = 120分钟
                ax.set_yticks(range(0, 121, 30))  # 每30分钟一个刻度
                ax.set_yticklabels(['0', '30分钟', '1小时', '1.5小时', '2小时'])
            else:
                # 无数据时显示占位符
                ax.text(0.5, 0.5, '暂无学习数据\n开始学习后将会显示时长分布', 
                       ha='center', va='center', fontsize=16, 
                       transform=ax.transAxes, color='#999999')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_xticks([])
                ax.set_yticks([])
            
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('学习时长 (分钟)', fontsize=12)
            ax.grid(axis='y', linestyle='--', alpha=0.5)
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True
        except Exception as e:
            print(f"生成时长分布图失败: {e}")
            return False
    
    @staticmethod
    def generate_heatmap(heatmap_data, year, month, save_path="heatmap.png"):
        """
        生成学习热力图
        
        Args:
            heatmap_data: {date: count}
            year: 年份
            month: 月份
            save_path: 保存路径
            
        Returns:
            bool: 是否成功
        """
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
                        ax.text(j, i, str(heatmap_array[i][j]), 
                               ha="center", va="center", 
                               color="black", fontsize=8)
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True
        except Exception as e:
            print(f"生成热力图失败: {e}")
            return False
    
    @staticmethod
    def generate_session_accuracy_trend(session_stats, save_path="session_accuracy_trend.png"):
        """生成按场次的正确率趋势图"""
        try:
            # 按日期分组，生成"今日第X次"或"X月X日第X次"标签
            date_groups = {}  # {date_str: [(label, accuracy), ...]}
            
            if session_stats:
                for stat in session_stats:
                    end_time = stat.get('end_time', '')
                    accuracy = stat.get('accuracy', 0)
                    
                    # 解析日期
                    if end_time:
                        try:
                            if isinstance(end_time, str):
                                dt = datetime.strptime(end_time[:19], "%Y-%m-%d %H:%M:%S")
                            else:
                                dt = end_time
                            date_str = dt.strftime("%m月%d日")
                            time_str = dt.strftime("%H:%M")
                        except:
                            date_str = "未知日期"
                            time_str = ""
                    else:
                        date_str = "未知日期"
                        time_str = ""
                    
                    if date_str not in date_groups:
                        date_groups[date_str] = []
                    date_groups[date_str].append((time_str, accuracy))
            
            # 生成标签和数据点
            sessions = []
            accuracies = []
            
            # 按日期排序（从早到晚）
            for date_str in sorted(date_groups.keys()):
                games = date_groups[date_str]
                for i, (time_str, acc) in enumerate(games):
                    if date_str == datetime.now().strftime("%m月%d日"):
                        sessions.append(f"今日第{i+1}次")
                    else:
                        sessions.append(f"{date_str}\n第{i+1}次")
                    accuracies.append(acc)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if sessions:
                ax.plot(sessions, accuracies, marker='o', linewidth=2, markersize=8,
                       color='#9C27B0', label='正确率')
                ax.fill_between(sessions, accuracies, alpha=0.3, color='#9C27B0')
                ax.set_title('学习场次正确率趋势', fontsize=16, fontweight='bold')
                ax.legend(loc='best')
                ax.set_ylim(0, 100)
            else:
                ax.text(0.5, 0.5, '暂无学习数据\n开始学习后将会显示趋势图',
                       ha='center', va='center', fontsize=16,
                       transform=ax.transAxes, color='#999999')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_xticks([])
                ax.set_yticks([])
            
            ax.set_xlabel('学习场次', fontsize=12)
            ax.set_ylabel('正确率 (%)', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True
        except Exception as e:
            print(f"生成场次趋势图失败: {e}")
            return False
    
    @staticmethod
    def generate_session_duration_chart(session_stats, save_path="session_duration.png"):
        """生成按场次的学习时长分布图"""
        try:
            # 按日期分组，生成"今日第X次"或"X月X日第X次"标签
            date_groups = {}  # {date_str: [(label, duration), ...]}
            
            if session_stats:
                for stat in session_stats:
                    end_time = stat.get('end_time', '')
                    duration = stat.get('duration', 0) / 60  # 转换为分钟
                    
                    # 解析日期
                    if end_time:
                        try:
                            if isinstance(end_time, str):
                                dt = datetime.strptime(end_time[:19], "%Y-%m-%d %H:%M:%S")
                            else:
                                dt = end_time
                            date_str = dt.strftime("%m月%d日")
                            time_str = dt.strftime("%H:%M")
                        except:
                            date_str = "未知日期"
                            time_str = ""
                    else:
                        date_str = "未知日期"
                        time_str = ""
                    
                    if date_str not in date_groups:
                        date_groups[date_str] = []
                    date_groups[date_str].append((time_str, duration))
            
            # 生成标签和数据点
            sessions = []
            durations = []
            
            # 按日期排序（从早到晚）
            for date_str in sorted(date_groups.keys()):
                games = date_groups[date_str]
                for i, (time_str, dur) in enumerate(games):
                    if date_str == datetime.now().strftime("%m月%d日"):
                        sessions.append(f"今日第{i+1}次")
                    else:
                        sessions.append(f"{date_str}\n第{i+1}次")
                    durations.append(dur)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if sessions:
                bars = ax.bar(sessions, durations, color='#2196F3', alpha=0.8)
                ax.set_title('学习场次时长分布', fontsize=16, fontweight='bold')
                
                for bar, duration in zip(bars, durations):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{duration:.1f}分钟',
                           ha='center', va='bottom', fontsize=10)
                
                ax.set_ylim(0, 20)  # 最多20分钟
                ax.set_yticks(range(0, 21, 5))  # 每5分钟一个刻度
                ax.set_yticklabels(['0', '5分钟', '10分钟', '15分钟', '20分钟'])
                ax.legend(loc='best')
            else:
                ax.text(0.5, 0.5, '暂无学习数据\n开始学习后将会显示时长分布',
                       ha='center', va='center', fontsize=16,
                       transform=ax.transAxes, color='#999999')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_xticks([])
                ax.set_yticks([])
            
            ax.set_xlabel('学习场次', fontsize=12)
            ax.set_ylabel('学习时长 (分钟)', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True
        except Exception as e:
            print(f"生成场次时长图失败: {e}")
            return False
    
    @staticmethod
    def generate_session_wrong_trend(wrong_history, save_path="session_wrong_trend.png"):
        """生成按场次的错词下降曲线"""
        try:
            # 按日期分组，生成"今日第X次"或"X月X日第X次"标签
            date_groups = {}  # {date_str: [(label, wrong_percentage), ...]}
            
            if wrong_history:
                for stat in wrong_history:
                    end_time = stat.get('end_time', '')
                    wrong_count = stat.get('wrong_count', 0)
                    total_count = stat.get('total_count', 1)
                    
                    # 计算错词百分比
                    wrong_pct = (wrong_count / total_count * 100) if total_count > 0 else 0
                    
                    # 解析日期
                    if end_time:
                        try:
                            if isinstance(end_time, str):
                                dt = datetime.strptime(end_time[:19], "%Y-%m-%d %H:%M:%S")
                            else:
                                dt = end_time
                            date_str = dt.strftime("%m月%d日")
                            time_str = dt.strftime("%H:%M")
                        except:
                            date_str = "未知日期"
                            time_str = ""
                    else:
                        date_str = "未知日期"
                        time_str = ""
                    
                    if date_str not in date_groups:
                        date_groups[date_str] = []
                    date_groups[date_str].append((time_str, wrong_pct))
            
            # 生成标签和数据点
            sessions = []
            wrong_percentages = []
            
            # 按日期排序（从早到晚）
            for date_str in sorted(date_groups.keys()):
                games = date_groups[date_str]
                for i, (time_str, pct) in enumerate(games):
                    if date_str == datetime.now().strftime("%m月%d日"):
                        sessions.append(f"今日第{i+1}次")
                    else:
                        sessions.append(f"{date_str}\n第{i+1}次")
                    wrong_percentages.append(pct)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if sessions:
                ax.plot(sessions, wrong_percentages, marker='o', linewidth=2, markersize=8,
                       color='#F44336', label='错词率')
                ax.fill_between(sessions, wrong_percentages, alpha=0.3, color='#F44336')
                ax.set_title('学习场次错词下降曲线', fontsize=16, fontweight='bold')
                ax.legend(loc='best')
                ax.set_ylim(0, 100)  # 百分比 0-100%
            else:
                ax.text(0.5, 0.5, '暂无错词数据\n答错单词后将会显示曲线',
                       ha='center', va='center', fontsize=16,
                       transform=ax.transAxes, color='#999999')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_xticks([])
                ax.set_yticks([])
            
            ax.set_xlabel('学习场次', fontsize=12)
            ax.set_ylabel('错词率 (%)', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True
        except Exception as e:
            print(f"生成场次错词曲线失败: {e}")
            return False
    
    @staticmethod
    def generate_session_progress_chart(session_stats, save_path="session_progress.png"):
        """生成按场次的学习进度图"""
        try:
            # 按日期分组，生成"今日第X次"或"X月X日第X次"标签
            date_groups = {}  # {date_str: [(label, total, correct), ...]}
            
            if session_stats:
                for stat in session_stats:
                    end_time = stat.get('end_time', '')
                    total = stat.get('total_count', 0)
                    correct = int(total * stat.get('accuracy', 0) / 100)
                    
                    # 解析日期
                    if end_time:
                        try:
                            if isinstance(end_time, str):
                                dt = datetime.strptime(end_time[:19], "%Y-%m-%d %H:%M:%S")
                            else:
                                dt = end_time
                            date_str = dt.strftime("%m月%d日")
                            time_str = dt.strftime("%H:%M")
                        except:
                            date_str = "未知日期"
                            time_str = ""
                    else:
                        date_str = "未知日期"
                        time_str = ""
                    
                    if date_str not in date_groups:
                        date_groups[date_str] = []
                    date_groups[date_str].append((time_str, total, correct))
            
            # 生成标签和数据点
            sessions = []
            total_words = []
            correct_words = []
            
            # 按日期排序（从早到晚）
            for date_str in sorted(date_groups.keys()):
                games = date_groups[date_str]
                for i, (time_str, total, correct) in enumerate(games):
                    if date_str == datetime.now().strftime("%m月%d日"):
                        sessions.append(f"今日第{i+1}次")
                    else:
                        sessions.append(f"{date_str}\n第{i+1}次")
                    total_words.append(total)
                    correct_words.append(correct)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if sessions:
                x = range(len(sessions))
                width = 0.35
                
                bars1 = ax.bar([i - width/2 for i in x], total_words, width,
                             label='总题数', color='#2196F3', alpha=0.8)
                bars2 = ax.bar([i + width/2 for i in x], correct_words, width,
                             label='正确数', color='#4CAF50', alpha=0.8)
                
                ax.set_title('学习场次进度对比', fontsize=16, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels(sessions)
                ax.legend(loc='best')
            else:
                ax.text(0.5, 0.5, '暂无学习数据\n开始学习后将会显示进度图',
                       ha='center', va='center', fontsize=16,
                       transform=ax.transAxes, color='#999999')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_xticks([])
                ax.set_yticks([])
            
            ax.set_xlabel('学习场次', fontsize=12)
            ax.set_ylabel('单词数', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            ax.grid(True, linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True
        except Exception as e:
            print(f"生成场次进度图失败: {e}")
            return False
