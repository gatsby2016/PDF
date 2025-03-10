import os
import time
import schedule
from datetime import datetime

from config import UPDATE_FREQUENCY, PDF_STORAGE_PATH, SUMMARY_STORAGE_PATH, SOCIAL_POST_PATH, SHOW_IMAGE_PREVIEW, MANUAL_PDF_LINKS
from scrapers.arxiv_scraper import ArxivScraper
from scrapers.biorxiv_scraper import BiorxivScraper
from scrapers.medrxiv_scraper import MedrxivScraper
from processors.pdf_processor import PDFProcessor
from processors.llm_processor import LLMProcessor
from generators.summary_generator import SummaryGenerator
from generators.social_post_generator import SocialPostGenerator
from processors.manual_link_processor import ManualLinkProcessor
import matplotlib.pyplot as plt
from PIL import Image

def create_directories():
    """创建必要的目录"""
    for path in [PDF_STORAGE_PATH, SUMMARY_STORAGE_PATH, SOCIAL_POST_PATH]:
        if not os.path.exists(path):
            os.makedirs(path)

def run_pipeline():
    """运行完整的处理流程"""
    print(f"开始运行 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化组件
    arxiv_scraper = ArxivScraper()
    biorxiv_scraper = BiorxivScraper()
    medrxiv_scraper = MedrxivScraper()
    pdf_processor = PDFProcessor()
    llm_processor = LLMProcessor()
    summary_generator = SummaryGenerator()
    social_post_generator = SocialPostGenerator()
    manual_link_processor = ManualLinkProcessor()  # 新增
    
    # 1. 获取文章元数据
    print("正在获取arXiv文章...")
    arxiv_papers = arxiv_scraper.fetch_papers()
    
    print("正在获取bioRxiv文章...")
    biorxiv_papers = biorxiv_scraper.fetch_papers()
    
    print("正在获取medRxiv文章...")
    medrxiv_papers = medrxiv_scraper.fetch_papers()
    
    # 处理手动指定的PDF链接
    print("正在处理手动指定的PDF链接...")
    manual_papers = manual_link_processor.process_links(MANUAL_PDF_LINKS)
    
    # 合并所有论文
    all_papers = arxiv_papers + biorxiv_papers + medrxiv_papers + manual_papers
    print(f"共获取到 {len(all_papers)} 篇文章")
    
    # 2. 处理每篇文章
    for i, paper in enumerate(all_papers, 1):
        try:
            print(f"\n处理第 {i}/{len(all_papers)} 篇文章: {paper['title']}")
            
            # 下载PDF
            print("- 下载PDF...")
            pdf_path = pdf_processor.download_pdf(paper)
            
            # 提取PDF内容
            print("- 提取PDF内容...")
            pdf_content = pdf_processor.extract_content(pdf_path)
            pdf_images = pdf_processor.extract_images(pdf_path)
            
            # 人工干预确认
            print("\n" + "="*50)
            print(f"论文标题: {paper['title']}")
            print(f"作者: {', '.join(paper['authors'])}")
            print(f"摘要: {paper['abstract'][:200]}...")
            
            # 显示提取的内容预览
            content_preview = pdf_content[:500] + "..." if len(pdf_content) > 500 else pdf_content
            print(f"\nPDF内容预览:\n{content_preview}")
            
            # 显示图片信息和预览
            if pdf_images:
                print(f"\n提取到 {len(pdf_images)} 张图片:")
                for i, img_path in enumerate(pdf_images[:3], 1):
                    print(f"  图片 {i}: {os.path.basename(img_path)}")
                if len(pdf_images) > 3:
                    print(f"  ... 以及其他 {len(pdf_images) - 3} 张图片")
                
                # 根据配置决定是否显示图像预览
                if SHOW_IMAGE_PREVIEW:
                    fig, axes = plt.subplots(1, min(3, len(pdf_images)), figsize=(15, 5))
                    if len(pdf_images) == 1:
                        axes = [axes]
                    
                    for i, (img_path, ax) in enumerate(zip(pdf_images[:3], axes), 1):
                        try:
                            img = Image.open(img_path)
                            ax.imshow(img)
                            ax.axis('off')
                            ax.set_title(f"图片 {i}")
                        except Exception as e:
                            print(f"  无法显示图片 {i}: {str(e)}")
                    
                    plt.tight_layout()
                    plt.show()
            else:
                print("\n未提取到图片")
            
            # 请求用户确认
            print("\n是否继续处理该论文? (y/n): ", end="")
            user_input = input().strip().lower()
            
            if user_input != 'y':
                print("✗ 用户选择跳过该论文")
                skipped_log_path = os.path.join(SUMMARY_STORAGE_PATH, "user_skipped_papers.log")
                with open(skipped_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {paper['title']} - 用户手动跳过\n")
                continue
            
            # 生成综述
            print("- 生成/读取论文综述...")
            summary_result = summary_generator.generate_summary(paper, pdf_content)
            
            # 检查论文评估结果
            if summary_result is None:
                print("✗ 论文评估未通过，跳过后续处理")
                # 记录被跳过的论文信息
                skipped_log_path = os.path.join(SUMMARY_STORAGE_PATH, "skipped_papers.log")
                with open(skipped_log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {paper['title']} - 评估未通过\n")
                continue
            
            # 如果通过评估，提取摘要内容
            summary = summary_result
            
            # 生成社交媒体文案
            print("- 生成社交媒体文案...")
            social_post = social_post_generator.generate_post(paper, summary, pdf_images)
            
            print(f"✓ 完成文章处理: {paper['title']}")
        except Exception as e:
            print(f"✗ 处理文章时出错: {paper['title']}, 错误: {str(e)}")
    
    print(f"运行完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """主函数"""
    create_directories()
    
    # 立即运行一次
    run_pipeline()
    
    # 设置定时任务
    schedule.every(UPDATE_FREQUENCY).hours.do(run_pipeline)
    
    # 保持程序运行
    while False:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()