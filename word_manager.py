"""
词库管理模块
负责单词文件的扫描、加载和导入功能
"""
import os
from database import DatabaseManager


class WordManager:
    """词库管理器，处理人教版年级单词和用户自定义单词"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.wordlists_dir = "wordlists"
        # 获取项目根目录（本文件所在目录）
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.grade_levels = [
            "三年级上", "三年级下",
            "四年级上", "四年级下",
            "五年级上", "五年级下",
            "六年级上", "六年级下"
        ]
        # 确保词库目录存在
        self._ensure_wordlists_dir()
        # 启动时清理自定义单词（让用户每次重新导入）
        self._cleanup_custom_words()
    
    def _cleanup_custom_words(self):
        """清理自定义单词，下次启动需要重新导入"""
        # 删除根目录的words.txt文件（如果存在）
        words_txt = os.path.join(self.base_dir, "words.txt")
        if os.path.exists(words_txt):
            try:
                os.remove(words_txt)
                print(f"已删除自定义单词文件: {words_txt}")
            except Exception as e:
                print(f"删除 words.txt 失败: {e}")
        
        # 可选：也清除数据库中的自定义单词（让用户每次重新导入）
        # 如果需要保留数据库中的自定义单词，可以注释掉这行
        # self.db.clear_custom_words()
    
    def _ensure_wordlists_dir(self):
        """确保词库目录存在，如果不存在则创建并生成示例文件"""
        if not os.path.exists(self.wordlists_dir):
            os.makedirs(self.wordlists_dir)
            print(f"创建词库目录: {self.wordlists_dir}")
            self._create_sample_wordlist()
    
    def _create_sample_wordlist(self):
        """创建示例单词文件"""
        sample_file = os.path.join(self.wordlists_dir, "三年级上.txt")
        if not os.path.exists(sample_file):
            with open(sample_file, "w", encoding="utf-8") as f:
                f.write("apple,苹果\n")
                f.write("book,书;书本\n")
                f.write("cat,猫;猫咪\n")
                f.write("dog,狗;小狗\n")
                f.write("egg,鸡蛋;蛋\n")
            print(f"创建示例单词文件: {sample_file}")
    
    def scan_and_import_wordlists(self):
        """扫描词库目录并导入所有单词文件"""
        total_imported = 0

        # 注意：不再自动导入 words.txt，自定义单词需要手动导入
        # 扫描词库目录（年级词库）
        wordlists_path = os.path.join(self.base_dir, self.wordlists_dir)
        if not os.path.exists(wordlists_path):
            return total_imported
        
        for filename in os.listdir(wordlists_path):
            if filename.endswith(".txt"):
                grade_level = filename.replace(".txt", "")
                filepath = os.path.join(wordlists_path, filename)
                count = self.import_wordlist(filepath, grade_level)
                total_imported += count
                print(f"导入 {filename}: {count} 个单词")
        
        return total_imported
    
    def _import_words_from_file(self, filepath, source_type, grade_level=None):
        """
        通用的单词导入方法
        
        Args:
            filepath: 单词文件路径
            source_type: 来源类型 ('builtin' 或 'custom')
            grade_level: 年级级别（仅builtin需要）
            
        Returns:
            int: 成功导入的单词数量
        """
        words = []
        error_lines = []
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            file_content = None
            
            for encoding in encodings:
                try:
                    with open(filepath, "r", encoding=encoding) as f:
                        file_content = f.readlines()
                    print(f"成功读取文件 {filepath}，编码: {encoding}")
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if file_content is None:
                print(f"无法读取文件 {filepath}，尝试了所有编码")
                return 0
            
            line_num = 0
            for line in file_content:
                line_num += 1
                line = line.strip()
                if not line:
                    continue
                
                # 支持逗号、制表符或空格分隔
                parts = None
                if ',' in line:
                    parts = line.split(",")
                elif '\t' in line:
                    parts = line.split("\t")
                elif ' ' in line:
                    parts = line.split(None, 1)
                else:
                    parts = line.split()
                
                if len(parts) >= 2:
                    english = parts[0].strip()
                    # 多个中文释义用分号连接
                    chinese = ";".join([m.strip() for m in parts[1:] if m.strip()])
                    
                    if english and chinese:
                        words.append((english, chinese))
                    else:
                        error_lines.append(f"行{line_num}: 英文或中文为空 - '{line}'")
                else:
                    error_lines.append(f"行{line_num}: 分隔失败，parts数量={len(parts)} - '{line}'")
            
            # 显示解析错误
            if error_lines:
                print(f"文件 {filepath} 解析错误:")
                for err in error_lines[:5]:  # 只显示前5个错误
                    print(f"  {err}")
                if len(error_lines) > 5:
                    print(f"  ... 还有 {len(error_lines)-5} 个错误")
            
            # 批量导入数据库
            if words:
                print(f"从文件 {filepath} 解析出 {len(words)} 个单词")
                count = self.db.add_words_batch(words, source=source_type, grade_level=grade_level)
                print(f"成功导入 {count} 个单词到数据库")
                if count < len(words):
                    print(f"  注意: {len(words)-count} 个单词已存在，跳过导入")
                return count
            else:
                print(f"文件 {filepath} 没有有效单词")
                return 0
            
        except FileNotFoundError:
            print(f"文件不存在: {filepath}")
            return 0
        except Exception as e:
            print(f"导入单词文件失败 {filepath}: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def import_wordlist(self, filepath, grade_level=None):
        """导入内置单词文件到数据库（按年级）"""
        return self._import_words_from_file(filepath, 'builtin', grade_level)
    
    def import_custom_wordlist(self, filepath):
        """导入用户自定义单词本"""
        return self._import_words_from_file(filepath, 'custom')
    
    def get_words_for_grade(self, grade_level):
        """获取指定年级的单词列表"""
        return self.db.get_words_by_grade(grade_level)
    
    def get_all_grades(self):
        """获取所有可用的年级列表"""
        return self.grade_levels
    
    def parse_word_meanings(self, chinese_str):
        """
        解析中文释义字符串为列表
        
        Args:
            chinese_str: 中文释义字符串（用分号分隔）
            
        Returns:
            list: 释义列表
        """
        if not chinese_str:
            return []
        return [m.strip() for m in chinese_str.split(";") if m.strip()]
