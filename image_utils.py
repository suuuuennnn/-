"""
图片工具模块
负责图片加载、创建默认图片和图片更换功能
"""
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os


class ImageUtils:
    """图片工具类，提供图片加载和生成功能"""
    
    def __init__(self):
        # 默认图片缓存
        self.images = {}
        # 获取项目根目录（本文件所在目录）
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # 外部图片路径配置
        self.external_images = {
            "mouse": ["laoshu1.png", "mouse.png", "mouse.gif", "mole.png", "地鼠.png"],
            "hammer": ["chuizi.png", "hammer.png", "hit.png", "锤子.png"],
            "runaway": ["runaway.png", "escape.png", "逃跑.png"],
            "injured": ["laoshu2.png", "injured.png", "hurt.png", "受伤.png"],
            "background": ["beijing.png", "background.png", "bg.png", "背景.png"]
        }
        # 默认尺寸
        self.sizes = {
            "mouse": 80,
            "hammer": 80,
            "runaway": 80,
            "injured": 80
        }
    
    def create_default_image(self, color, emoji, size=80):
        """
        创建带圆形背景和emoji的默认图片
        
        Args:
            color: 背景颜色（十六进制字符串）
            emoji: emoji字符
            size: 图片尺寸
            
        Returns:
            ImageTk.PhotoImage 对象
        """
        img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # 绘制圆形背景
        margin = 5
        draw.ellipse([margin, margin, size-margin, size-margin], fill=color)
        
        # 尝试加载emoji字体
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", size // 2)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size // 2)
            except:
                font = ImageFont.load_default()
        
        # 计算文本位置（居中）
        bbox = draw.textbbox((0, 0), emoji, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2 - bbox[0]
        y = (size - text_height) // 2 - bbox[1]
        
        # 绘制emoji
        draw.text((x, y), emoji, font=font, fill="white")
        
        return ImageTk.PhotoImage(img)
    
    def load_default_images(self):
        """加载所有默认图片"""
        self.images["mouse"] = self.create_default_image("#8B6914", "🐭", 80)
        self.images["hammer"] = self.create_default_image("#FF6347", "🔨", 80)
        self.images["runaway"] = self.create_default_image("#D2B48C", "💨", 80)
        self.images["injured"] = self.create_default_image("#CD5C5C", "😵", 80)
        print("默认图片加载完成")
    
    def load_external_images(self):
        """尝试加载外部图片文件，如果存在则覆盖默认图片"""
        # 搜索路径列表：项目根目录、tupian文件夹、以及tupian的子文件夹
        search_paths = [
            self.base_dir,  # 项目根目录
            os.path.join(self.base_dir, "tupian"),  # tupian文件夹
        ]
        
        # 检查tupian文件夹中的所有子文件夹
        tupian_dir = os.path.join(self.base_dir, "tupian")
        if os.path.exists(tupian_dir) and os.path.isdir(tupian_dir):
            for item in os.listdir(tupian_dir):
                subdir = os.path.join(tupian_dir, item)
                if os.path.isdir(subdir):
                    search_paths.append(subdir)
        
        for key, filenames in self.external_images.items():
            for filename in filenames:
                # 在所有搜索路径中查找图片
                for search_path in search_paths:
                    file_path = os.path.join(search_path, filename)
                    if os.path.exists(file_path):
                        try:
                            img = Image.open(file_path)
                            if key == "background":
                                self.images[key] = ImageTk.PhotoImage(img)
                                print(f"成功加载背景图片: {file_path} ({img.width}x{img.height})")
                            else:
                                size = self.sizes.get(key, 80)
                                img = img.resize((size, size), Image.Resampling.LANCZOS)
                                self.images[key] = ImageTk.PhotoImage(img)
                                print(f"成功加载外部图片: {file_path} ({size}x{size})")
                            break
                        except Exception as e:
                            print(f"加载外部图片失败 {file_path}: {e}")
    
    def get_image(self, image_type):
        """获取指定类型的图片"""
        return self.images.get(image_type)
    
    def change_image(self, image_type, file_path):
        """
        更换指定类型的图片
        
        Args:
            image_type: 图片类型 (mouse/hammer/runaway/injured)
            file_path: 图片文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            size = self.sizes.get(image_type, 80)
            img = Image.open(file_path)
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            self.images[image_type] = ImageTk.PhotoImage(img)
            print(f"图片更换成功: {image_type} -> {file_path}")
            return True
        except Exception as e:
            print(f"图片更换失败: {e}")
            return False
    
    def load_all_images(self):
        """加载所有图片（先加载默认，再尝试加载外部）"""
        self.load_default_images()
        self.load_external_images()
