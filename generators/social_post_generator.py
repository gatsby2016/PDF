import os
import json
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import textwrap
from config import SOCIAL_POST_PATH, SOCIAL_POST_MAX_TOKENS
from processors.llm_processor import LLMProcessor

class SocialPostGenerator:
    def __init__(self):
        self.storage_path = SOCIAL_POST_PATH
        self.llm_processor = LLMProcessor()
        self.max_tokens = SOCIAL_POST_MAX_TOKENS
    
    def _select_key_image(self, images):
        """选择关键主图"""
        if not images:
            return None
            
        # 优先选择第一页的第一张图片（通常是主图）
        page1_images = [img for img in images if "page_1_" in img]
        if page1_images:
            return page1_images[0]
            
        # 如果第一页没有图片，选择最大的图片文件（可能是重要图表）
        return max(images, key=lambda x: os.path.getsize(x))
    
    def generate_post(self, paper, summary, images):
        """生成社交媒体文案"""
        # 构建提示词
        prompt = f"""
请根据以下学术论文的综述，生成一条适合在社交媒体（如小红书、微博）上分享的简短文案（不超过300字）：

论文标题: {paper['title']}
论文综述:
{summary}

要求:
1. 使用吸引人的开头，引起读者兴趣，但不能浮夸
2. 着重突出论文的主要方法和创新点，以及关键发现和结果，一定要严谨专业
3. 最后可以提出一个专业的思考性问题或真实严谨的研究总结，不鼓励互动，但可以让读者思考
4. 可以加入四到五个相关的简洁的话题标签（hashtag）
5. 整个文案简洁明了，内容可以适当通俗，三百字左右

最后生成文案标题，用一句不超过20字的语句对该论文在领域内的影响进行概述，专业同时表达客观严谨的学术作风。
"""
        
        # 使用LLM生成文案
        post_text = self.llm_processor.process_text(prompt, self.max_tokens)

        # 生成一张带有论文标题和详细信息的图片
        paper_id = paper['id'].split('/')[-1] if '/' in paper['id'] else paper['id']
        title_slug = paper['title'][:50].replace(' ', '_').replace('/', '_').replace('\\', '_')
        title_slug = ''.join(c for c in title_slug if c.isalnum() or c in '_-')  # 只保留字母数字和下划线
        selected_image = self._create_title_image(paper['title'], paper, f"{paper_id}_{title_slug}")

        # 选择一张图片（如果有）
        selected_images = [selected_image]
        
        # 选择关键主图
        if images:
            # 更新图片选择逻辑，适应新的图片命名格式
            # 优先选择第一页的图片
            page1_images = [img for img in images if "figure_1_" in os.path.basename(img)]
            if page1_images:
                selected_images.append(page1_images[0])
            # 如果没有第一页的图片，选择最大的图片
            elif images:
                selected_images.append(max(images, key=lambda x: os.path.getsize(x)))
                    
        # 保存文案和图片信息
        file_name = f"{paper_id.replace('.', '_').replace(':', '_')}_post.json"
        file_path = os.path.join(self.storage_path, file_name)
        
        # 创建paper的副本并处理datetime对象
        paper_copy = paper.copy()
        for key, value in paper_copy.items():
            if isinstance(value, datetime):
                paper_copy[key] = value.isoformat()
        
        post_data = {
            'paper': paper_copy,
            'summary': summary,
            'post_text': post_text,
            'image_paths': selected_images,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(post_data, f, ensure_ascii=False, indent=2)
        
        return post_data
    
    def _create_title_image(self, title, paper, filename_prefix):
        """创建一张带有论文标题和详细信息的图片"""
        # 创建空白图片 - 纵向设计
        width, height = 800, 1200
        # 使用纯白背景
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        try:
            # 中文字体路径
            chinese_font_paths = [
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
            ]
            
            # 加载中文字体
            for font_path in chinese_font_paths:
                try:
                    title_font = ImageFont.truetype(font_path, 48)  # 标题字体稍微小一点，留出空间给其他信息
                    subtitle_font = ImageFont.truetype(font_path, 36)
                    info_font = ImageFont.truetype(font_path, 28)  # 信息字体
                    small_font = ImageFont.truetype(font_path, 24)
                    print(f"使用中文字体: {font_path}")
                    break
                except IOError:
                    continue
            
            if title_font is None:
                print("使用默认字体")
                title_font = subtitle_font = info_font = small_font = ImageFont.load_default()
                
        except Exception as e:
            print(f"加载字体出错: {str(e)}")
            title_font = subtitle_font = info_font = small_font = ImageFont.load_default()

        # 添加标题框
        title_box_margin = 40
        title_box = [(title_box_margin, height/5), (width-title_box_margin, height*3/4)]  # 调整标题框位置，留出更多空间
        draw.rectangle(title_box, outline=(100, 100, 100), width=3)
        
        # 绘制标题
        title_wrapped = textwrap.fill(title, width=25)
        draw.text((width/2, height/3), title_wrapped, font=title_font, fill=(0, 0, 0), anchor="mm", align="center")
        
        # 获取并格式化论文信息
        authors = "作者: " + ", ".join(paper.get('authors', ['未知']))[:80]
        if len(paper.get('authors', [])) > 3:
            authors = "作者: " + ", ".join(paper.get('authors', ['未知'])[:3]) + " 等"
            
        source = f"来源: {paper.get('source', '未知')}"
        
        # 格式化发布时间
        published = paper.get('published')
        if isinstance(published, datetime):
            published_str = f"发布时间: {published.strftime('%Y-%m-%d')}"
        elif isinstance(published, str):
            try:
                # 尝试解析ISO格式的日期字符串
                published_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                published_str = f"发布时间: {published_date.strftime('%Y-%m-%d')}"
            except:
                published_str = f"发布时间: {published}"
        else:
            published_str = "发布时间: 未知"
            
        # 获取PDF链接
        pdf_url = paper.get('pdf_url', '未提供')
        if len(pdf_url) > 50:  # 如果链接太长，截断显示
            pdf_url = pdf_url[:47] + "..."
        
        # 绘制论文信息
        info_y_start = height/2 + 50  # 从标题下方开始绘制信息
        line_spacing = 40  # 行间距
        
        # 绘制作者信息
        draw.text((width/2, info_y_start), authors, font=info_font, fill=(50, 50, 50), anchor="mm")
        
        # 绘制来源信息
        draw.text((width/2, info_y_start + line_spacing), source, font=info_font, fill=(50, 50, 50), anchor="mm")
        
        # 绘制发布时间
        draw.text((width/2, info_y_start + 2*line_spacing), published_str, font=info_font, fill=(50, 50, 50), anchor="mm")
        
        # 绘制PDF链接
        pdf_text = f"PDF链接: {pdf_url}"
        draw.text((width/2, info_y_start + 3*line_spacing), pdf_text, font=small_font, fill=(100, 100, 100), anchor="mm")
        
        # 底部文字
        draw.text((width/2, height-100), "由预印本文献订阅工具PDF自动生成", font=small_font, fill=(100, 100, 100), anchor="mm")
        draw.text((width/2, height-60), "每日学术精选", font=small_font, fill=(100, 100, 100), anchor="mm")
        
        # 添加简单的角落装饰
        corner_size = 50
        corner_color = (150, 150, 150)
        for pos in [(0, 0), (width, 0), (0, height), (width, height)]:
            draw.line([pos, (pos[0] + (corner_size if pos[0] == 0 else -corner_size), pos[1])], 
                     fill=corner_color, width=2)
            draw.line([pos, (pos[0], pos[1] + (corner_size if pos[1] == 0 else -corner_size))], 
                     fill=corner_color, width=2)
        
        # 保存图片
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        image_path = os.path.join(self.storage_path, f"{filename_prefix}_{timestamp}.png")
        image.save(image_path)
        
        return image_path