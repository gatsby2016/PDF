import os
import re
import requests
from urllib.parse import urlparse
import PyPDF2
from datetime import datetime
from bs4 import BeautifulSoup

class ManualLinkProcessor:
    """处理手动指定的PDF链接，提取元数据"""
    
    def __init__(self):
        pass
        
    def process_links(self, links):
        """处理链接列表，返回包含元数据的论文列表"""
        papers = []
        
        for link in links:
            try:
                print(f"正在处理手动链接: {link}")
                paper = self.extract_metadata(link)
                if paper:
                    papers.append(paper)
            except Exception as e:
                print(f"处理链接时出错: {link}, 错误: {str(e)}")
                
        return papers
    
    def extract_metadata(self, url):
        """从链接提取元数据"""
        # 解析URL获取基本信息
        parsed_url = urlparse(url)
        
        # 生成唯一ID
        paper_id = f"manual_{os.path.basename(parsed_url.path)}"
        
        # 检查链接类型并调用相应的处理方法
        if "arxiv.org" in url:
            return self._extract_arxiv_metadata(url, paper_id)
        elif "nature.com" in url:
            return self._extract_nature_metadata(url, paper_id)
        else:
            # 尝试获取PDF链接
            pdf_url = self._get_pdf_url(url)
            return self._extract_generic_pdf_metadata(pdf_url if pdf_url else url, paper_id)
    
    def _extract_nature_metadata(self, url, paper_id):
        """从Nature文章链接提取元数据"""
        try:
            # 发送请求获取网页内容
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                print(f"无法访问Nature文章页面: {response.status_code}")
                return self._create_fallback_metadata(url, paper_id)
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            title_elem = soup.find('h1', class_='c-article-title')
            title = title_elem.text.strip() if title_elem else "未知标题"
            
            # 提取作者
            authors = []
            author_elems = soup.select('ul.c-article-author-list li.c-article-author-list__item a[data-test="author-name"]')
            for author_elem in author_elems:
                authors.append(author_elem.text.strip())
            
            # 提取摘要
            abstract_elem = soup.find('div', class_='c-article-section__content', id=lambda x: x and 'Abs1' in x)
            if not abstract_elem:
                abstract_elem = soup.find('div', class_='c-article-teaser-text')
            abstract = abstract_elem.text.strip() if abstract_elem else "未找到摘要"
            
            # 提取发布日期
            date_elem = soup.find('time', itemprop='datePublished')
            published = date_elem['datetime'] if date_elem and 'datetime' in date_elem.attrs else datetime.now().strftime("%Y-%m-%d")
            
            # 获取PDF链接
            pdf_link = None
            pdf_elem = soup.find('a', attrs={'data-track-action': 'download pdf'})
            if pdf_elem and 'href' in pdf_elem.attrs:
                pdf_link = 'https://www.nature.com' + pdf_elem['href'] if pdf_elem['href'].startswith('/') else pdf_elem['href']
            
            # 如果找不到PDF链接，使用原始URL
            if not pdf_link:
                pdf_link = url
            
            # 提取主题分类
            categories = []
            subject_elems = soup.select('li.c-article-subject-list__subject')
            for subject in subject_elems:
                categories.append(subject.text.strip())
            
            # 如果没有找到分类，添加默认分类
            if not categories:
                categories = ["Nature Article"]
            
            return {
                'id': paper_id,
                'title': title,
                'authors': authors if authors else ["未知作者"],
                'abstract': abstract,
                'pdf_url': pdf_link,
                'published': published,
                'source': 'nature',
                'journal': self._extract_journal_info(soup),
                'categories': categories  # 确保添加categories字段
            }
            
        except Exception as e:
            print(f"从Nature网页提取元数据时出错: {str(e)}")
            return self._create_fallback_metadata(url, paper_id)
    
    def _extract_journal_info(self, soup):
        """从Nature网页提取期刊信息"""
        try:
            journal_elem = soup.find('i', class_='c-journal-title')
            if journal_elem:
                return journal_elem.text.strip()
            return "Nature Journal"
        except:
            return "Nature Journal"
    
    def _get_pdf_url(self, url):
        """尝试从文章页面获取PDF链接"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找可能的PDF链接
            pdf_links = soup.find_all('a', href=lambda href: href and href.endswith('.pdf'))
            if pdf_links:
                pdf_href = pdf_links[0]['href']
                # 处理相对链接
                if pdf_href.startswith('/'):
                    parsed_url = urlparse(url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    return base_url + pdf_href
                return pdf_href
                
            return None
        except:
            return None
    def _extract_arxiv_metadata(self, pdf_url, paper_id):
        """从arXiv PDF链接提取元数据"""
        # 将PDF链接转换为API链接
        arxiv_id = os.path.basename(pdf_url).replace('.pdf', '')
        api_url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
        
        try:
            # 检查本地是否有缓存
            from config import PDF_STORAGE_PATH
            pdf_filename = f"{paper_id}.pdf"
            local_pdf_path = os.path.join(PDF_STORAGE_PATH, pdf_filename)
            
            if os.path.exists(local_pdf_path):
                print(f"发现arXiv论文的本地缓存: {local_pdf_path}")
            
            response = requests.get(api_url)
            if response.status_code != 200:
                print(f"无法从arXiv API获取元数据: {response.status_code}")
                return self._extract_generic_pdf_metadata(pdf_url, paper_id)
            
            # 解析XML响应
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # 定义命名空间
            ns = {'atom': 'http://www.w3.org/2005/Atom',
                  'arxiv': 'http://arxiv.org/schemas/atom'}
            
            # 提取元数据
            entry = root.find('.//atom:entry', ns)
            if entry is None:
                print(f"未找到arXiv条目: {arxiv_id}")
                return self._extract_generic_pdf_metadata(pdf_url, paper_id)
            
            title = entry.find('./atom:title', ns).text.strip()
            
            # 提取作者
            authors = []
            for author in entry.findall('./atom:author/atom:name', ns):
                authors.append(author.text.strip())
            
            # 提取摘要
            abstract = entry.find('./atom:summary', ns).text.strip()
            
            # 提取发布日期
            published = entry.find('./atom:published', ns).text
            
            # 提取分类
            categories = []
            for category in entry.findall('./arxiv:primary_category', ns):
                categories.append(category.get('term'))
            
            return {
                'id': paper_id,
                'title': title,
                'authors': authors,
                'abstract': abstract,
                'pdf_url': pdf_url,
                'published': published,
                'source': 'arxiv',
                'categories': categories,
                'local_pdf_path': local_pdf_path if os.path.exists(local_pdf_path) else None
            }
            
        except Exception as e:
            print(f"从arXiv提取元数据时出错: {str(e)}")
            return self._extract_generic_pdf_metadata(pdf_url, paper_id)
    def _extract_generic_pdf_metadata(self, pdf_url, paper_id):
        """从通用PDF链接提取元数据"""
        try:
            # 检查本地是否有缓存
            from config import PDF_STORAGE_PATH
            pdf_filename = f"{paper_id}.pdf"
            local_pdf_path = os.path.join(PDF_STORAGE_PATH, pdf_filename)
            
            if os.path.exists(local_pdf_path):
                print(f"使用本地缓存的PDF文件: {local_pdf_path}")
                temp_pdf_path = local_pdf_path
            else:
                # 下载PDF
                print(f"下载PDF文件: {pdf_url}")
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(pdf_url, headers=headers, stream=True)
                
                if response.status_code != 200:
                    print(f"无法下载PDF: {response.status_code}")
                    return self._create_fallback_metadata(pdf_url, paper_id)
                
                # 保存PDF文件
                temp_pdf_path = os.path.join(PDF_STORAGE_PATH, pdf_filename)
                os.makedirs(os.path.dirname(temp_pdf_path), exist_ok=True)
                
                with open(temp_pdf_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                print(f"PDF已保存到: {temp_pdf_path}")
            
            # 从PDF提取元数据
            with open(temp_pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                
                # 尝试从PDF元数据中提取信息
                metadata = reader.metadata
                title = metadata.get('/Title', os.path.basename(pdf_url))
                
                # 如果没有标题，尝试从第一页提取
                if not title or title == os.path.basename(pdf_url):
                    first_page_text = reader.pages[0].extract_text()
                    # 尝试找到可能的标题（通常是第一页的第一行或几行）
                    lines = first_page_text.split('\n')
                    title = lines[0].strip() if lines else os.path.basename(pdf_url)
                
                # 尝试提取作者
                authors = []
                author_text = metadata.get('/Author', '')
                if author_text:
                    # 尝试分割作者字符串
                    authors = [a.strip() for a in re.split(r'[,;]', author_text)]
                
                # 尝试提取摘要
                abstract = ""
                for page_num in range(min(2, len(reader.pages))):
                    page_text = reader.pages[page_num].extract_text()
                    # 查找"Abstract"或"摘要"部分
                    abstract_match = re.search(r'(?:Abstract|摘要)[:\s]*(.*?)(?:\n\n|\n[A-Z][a-z]+:)', page_text, re.DOTALL)
                    if abstract_match:
                        abstract = abstract_match.group(1).strip()
                        break
                
                # 如果没有找到摘要，使用前几百个字符
                if not abstract:
                    abstract = first_page_text[:500] + "..."
            
            # 不删除文件，因为它现在是缓存
            
            return {
                'id': paper_id,
                'title': title,
                'authors': authors if authors else ["未知作者"],
                'abstract': abstract,
                'pdf_url': pdf_url,
                'published': datetime.now().strftime("%Y-%m-%d"),
                'source': 'manual',
                'categories': ["未分类"],
                'local_pdf_path': temp_pdf_path  # 添加本地PDF路径
            }
            
        except Exception as e:
            print(f"从PDF提取元数据时出错: {str(e)}")
            # 如果提取失败，返回基本元数据
            return self._create_fallback_metadata(pdf_url, paper_id)
    
    def _create_fallback_metadata(self, pdf_url, paper_id):
        """创建基本的元数据"""
        return {
            'id': paper_id,
            'title': os.path.basename(pdf_url).replace('.pdf', ''),
            'authors': ["未知作者"],
            'abstract': "无法提取摘要。",
            'pdf_url': pdf_url,
            'published': datetime.now().strftime("%Y-%m-%d"),
            'source': 'manual',
            'categories': ["未分类"]  # 添加默认categories字段
        }