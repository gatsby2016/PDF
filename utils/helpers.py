import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

def format_date(date_str):
    """格式化日期字符串"""
    try:
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%Y年%m月%d日')
    except:
        return date_str

def create_html_digest(summaries, post_path):
    """创建HTML格式的文献摘要"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>今日预印本文献摘要</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .paper { margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
            .title { font-size: 18px; font-weight: bold; color: #333; }
            .meta { font-size: 14px; color: #666; margin: 5px 0; }
            .summary { font-size: 15px; line-height: 1.5; }
            .source { font-size: 12px; color: #999; }
            .header { text-align: center; margin-bottom: 30px; }
            .date { font-size: 14px; color: #666; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>今日预印本文献摘要</h1>
            <p class="date">生成日期: """ + datetime.now().strftime('%Y年%m月%d日') + """</p>
        </div>
    """
    
    for summary_file in summaries:
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        paper = data['paper']
        summary_text = data['summary']
        
        html += f"""
        <div class="paper">
            <div class="title">{paper['title']}</div>
            <div class="meta">
                <span>作者: {', '.join(paper['authors'])}</span> | 
                <span>发布日期: {format_date(paper['published'])}</span> | 
                <span>来源: {paper['source'].upper()}</span>
            </div>
            <div class="summary">{summary_text.replace('\n', '<br>')}</div>
            <div class="source">
                <a href="{paper['pdf_url']}" target="_blank">原文链接</a>
            </div>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    # 保存HTML文件
    html_path = os.path.join(post_path, f"digest_{datetime.now().strftime('%Y%m%d')}.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return html_path

def send_email_digest(email_to, html_path, smtp_server, smtp_port, smtp_user, smtp_pass):
    """通过邮件发送文献摘要"""
    try:
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email_to
        msg['Subject'] = f"今日预印本文献摘要 - {datetime.now().strftime('%Y年%m月%d日')}"
        
        # 添加HTML内容
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # 发送邮件
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        
        print(f"摘要邮件已发送至 {email_to}")
        return True
    except Exception as e:
        print(f"发送邮件时出错: {str(e)}")
        return False

def generate_social_media_batch(post_files):
    """生成一批社交媒体文案"""
    posts = []
    for post_file in post_files:
        try:
            with open(post_file, 'r', encoding='utf-8') as f:
                post_data = json.load(f)
            posts.append({
                'text': post_data['post_text'],
                'image': post_data['image_path'],
                'paper_title': post_data['paper']['title'],
                'paper_url': post_data['paper']['pdf_url']
            })
        except Exception as e:
            print(f"处理社交媒体文案时出错: {str(e)}")
    
    return posts

def find_latest_files(directory, file_pattern, max_count=10):
    """查找目录中最新的文件"""
    files = [os.path.join(directory, f) for f in os.listdir(directory) 
             if os.path.isfile(os.path.join(directory, f)) and file_pattern in f]
    
    # 按修改时间排序
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    return files[:max_count]

def create_weekly_digest(summary_path, output_path):
    """创建每周文献摘要"""
    # 获取过去7天的摘要文件
    today = datetime.now()
    weekly_files = []
    
    for i in range(7):
        date_str = (today - datetime.timedelta(days=i)).strftime('%Y%m%d')
        daily_digest = os.path.join(summary_path, f"digest_{date_str}.html")
        if os.path.exists(daily_digest):
            weekly_files.append(daily_digest)
    
    if not weekly_files:
        print("没有找到过去一周的摘要文件")
        return None
    
    # 合并HTML内容
    combined_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>每周预印本文献摘要</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .day-section { margin-bottom: 40px; }
            .day-header { background-color: #f5f5f5; padding: 10px; margin-bottom: 20px; }
            .paper { margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
            .title { font-size: 18px; font-weight: bold; color: #333; }
            .meta { font-size: 14px; color: #666; margin: 5px 0; }
            .summary { font-size: 15px; line-height: 1.5; }
            .source { font-size: 12px; color: #999; }
            .header { text-align: center; margin-bottom: 30px; }
            .date { font-size: 14px; color: #666; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>每周预印本文献摘要</h1>
            <p class="date">生成日期: """ + today.strftime('%Y年%m月%d日') + """</p>
        </div>
    """
    
    for html_file in weekly_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取日期和内容部分
        date_str = os.path.basename(html_file).replace('digest_', '').replace('.html', '')
        date_obj = datetime.strptime(date_str, '%Y%m%d')
        formatted_date = date_obj.strftime('%Y年%m月%d日')
        
        # 提取文章部分
        import re
        papers = re.findall(r'<div class="paper">.*?</div>\s*</div>', content, re.DOTALL)
        
        if papers:
            combined_html += f"""
            <div class="day-section">
                <div class="day-header">
                    <h2>{formatted_date}</h2>
                </div>
            """
            
            for paper in papers:
                combined_html += paper
            
            combined_html += "</div>"
    
    combined_html += """
    </body>
    </html>
    """
    
    # 保存合并后的HTML
    output_file = os.path.join(output_path, f"weekly_digest_{today.strftime('%Y%m%d')}.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined_html)
    
    return output_file