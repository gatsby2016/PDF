import os
import requests
import PyPDF2
import fitz  # PyMuPDF
from PIL import Image
import io
import hashlib
from config import PDF_STORAGE_PATH

class PDFProcessor:
    def __init__(self):
        self.storage_path = PDF_STORAGE_PATH
    
    def download_pdf(self, paper):
        """下载论文PDF"""
        # 检查是否已有本地缓存
        if "local_pdf_path" in paper and paper["local_pdf_path"] and os.path.exists(paper["local_pdf_path"]):
            print(f"使用本地缓存的PDF文件: {paper['local_pdf_path']}")
            return paper["local_pdf_path"]
        
        # 如果没有缓存，则下载PDF
        pdf_url = paper["pdf_url"]
        paper_id = paper["id"]
        
        # 处理arXiv URL，确保获取正确的ID
        if "arxiv.org" in pdf_url:
            # 从URL中提取arXiv ID
            import re
            arxiv_id_match = re.search(r'(\d+\.\d+)(v\d+)?', pdf_url)
            if arxiv_id_match:
                arxiv_id = arxiv_id_match.group(1)
                if arxiv_id_match.group(2):  # 如果有版本号
                    arxiv_id += arxiv_id_match.group(2)
                paper_id = f"arxiv_{arxiv_id}"
        
        # 构建保存路径，确保文件名有效
        pdf_filename = f"{paper_id.replace('/', '_').replace(':', '_')}.pdf"
        pdf_path = os.path.join(PDF_STORAGE_PATH, pdf_filename)
        
        # 如果文件已存在，直接返回路径
        if os.path.exists(pdf_path):
            print(f"PDF文件已存在: {pdf_path}")
            return pdf_path
        
        # 下载PDF
        print(f"下载PDF: {pdf_url}")
        try:
            # 设置请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # 发送请求
            response = requests.get(pdf_url, headers=headers, stream=True)
            response.raise_for_status()
            
            # 保存PDF
            with open(pdf_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"PDF下载完成: {pdf_path}")
            return pdf_path
        
        except Exception as e:
            print(f"下载PDF时出错: {str(e)}")
            return None
    
    def extract_content(self, pdf_path):
        """提取PDF文本内容"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"提取PDF文本时出错: {str(e)}")
            return ""
    
    def extract_images(self, pdf_path):
        """从PDF中提取每一页作为图片"""
        # 从PDF路径中获取论文ID
        pdf_name = os.path.basename(pdf_path)
        paper_id = pdf_name.replace('.pdf', '')
        
        # 在images目录下创建以论文ID命名的子目录
        output_dir = os.path.join(os.path.dirname(pdf_path), "images", paper_id)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 提取图片
        images = []
        
        try:
            # 使用PyMuPDF提取整页图像
            doc = fitz.open(pdf_path)
            
            for page_index in range(len(doc)):
                page = doc[page_index]
                
                # 将页面渲染为高质量图像
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x缩放以获得更好的质量
                page_image_filename = f"page_{page_index + 1}.png"
                page_image_path = os.path.join(output_dir, page_image_filename)
                
                # 保存图像
                pix.save(page_image_path)
                images.append(page_image_path)
                
                print(f"已保存第 {page_index + 1} 页图像: {page_image_path}")
            
            doc.close()
            
        except Exception as e:
            print(f"提取PDF页面图像时出错: {str(e)}")
        
        return images
    
    def get_metadata(self, pdf_path):
        """获取PDF元数据"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                metadata = reader.metadata
                return {
                    'title': metadata.get('/Title', ''),
                    'author': metadata.get('/Author', ''),
                    'subject': metadata.get('/Subject', ''),
                    'keywords': metadata.get('/Keywords', ''),
                    'creator': metadata.get('/Creator', ''),
                    'producer': metadata.get('/Producer', ''),
                    'creation_date': metadata.get('/CreationDate', ''),
                    'modification_date': metadata.get('/ModDate', ''),
                    'page_count': len(reader.pages)
                }
        except Exception as e:
            print(f"获取PDF元数据时出错: {str(e)}")
            return {}