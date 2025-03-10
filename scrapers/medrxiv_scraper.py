import os
import requests
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import json
import time
from functools import wraps
from config import SEARCH_KEYWORDS, PAPER_SEARCH_DAYS, MAX_RESULTS, PDF_STORAGE_PATH, KEYWORD_FILTER
from utils.keyword_filter import filter_papers_by_keywords

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def retry_multi(max_retries=5, delay=3):
    """重试装饰器，用于网络请求失败时自动重试"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            num_retries = 0
            while num_retries <= max_retries:
                try:
                    ret = func(*args, **kwargs)
                    if ret is None:
                        time.sleep(delay)
                        num_retries += 1
                        continue
                    return ret
                except requests.exceptions.RequestException as e:
                    if num_retries == max_retries:
                        logger.error(f"达到最大重试次数 {max_retries}，请求失败: {str(e)}")
                        raise
                    num_retries += 1
                    logger.warning(f"请求失败，正在进行第 {num_retries} 次重试: {str(e)}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


class MedrxivScraper:
    """medRxiv预印本平台爬虫，基于paperscraper项目格式重写"""
    
    def __init__(self):
        self.name = "medrxiv"
        self.base_url = "https://www.medrxiv.org"
        self.search_url = f"{self.base_url}/search"
        self.api_base_url = "https://api.biorxiv.org"
        self.api_papers_url = f"{self.api_base_url}/details/medrxiv/{{start_date}}/{{end_date}}/{{cursor}}"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        self.launch_date = "2019-06-01"  # medRxiv启动日期
    
    def _format_date(self, date_str):
        """格式化日期字符串"""
        try:
            # 尝试多种日期格式
            date_formats = [
                "%B %d, %Y",  # 例如: January 1, 2023
                "%b %d, %Y",  # 例如: Jan 1, 2023
                "%Y-%m-%d",   # 例如: 2023-01-01
                "%d %B %Y",   # 例如: 1 January 2023
                "%d %b %Y"    # 例如: 1 Jan 2023
            ]
            
            for date_format in date_formats:
                try:
                    date_obj = datetime.strptime(date_str, date_format)
                    return date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    continue
                
            # 如果所有格式都失败，尝试提取日期
            date_match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
            if date_match:
                year, month, day = date_match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                
            raise ValueError(f"无法解析日期格式: {date_str}")
            
        except Exception as e:
            logger.error(f"日期格式化错误: {str(e)}")
            return datetime.now().strftime("%Y-%m-%d")
    
    def _get_date_range(self):
        """获取搜索的日期范围"""
        days = PAPER_SEARCH_DAYS
        date_since = datetime.now() - timedelta(days=days)
        return date_since.strftime("%Y-%m-%d")
    
    def _build_query_string(self, keywords):
        """构建搜索查询字符串
        
        参数:
            keywords (list): 关键词配置列表
            
        返回:
            str: 格式化的查询字符串
        """
        query_parts = []
        
        for keyword_group in keywords:
            if keyword_group["type"] == "AND":
                # 对于AND类型，使用AND连接关键词
                terms = []
                for kw in keyword_group["keywords"]:
                    if ' ' in kw:
                        terms.append(f'"{kw}"')  # 带空格的关键词用引号包围
                    else:
                        terms.append(kw)
                
                if len(terms) > 1:
                    query_parts.append(f"({' AND '.join(terms)})")
                else:
                    query_parts.append(terms[0])
            else:  # OR
                # 对于OR类型，使用OR连接关键词
                terms = []
                for kw in keyword_group["keywords"]:
                    if ' ' in kw:
                        terms.append(f'"{kw}"')  # 带空格的关键词用引号包围
                    else:
                        terms.append(kw)
                
                if len(terms) > 1:
                    query_parts.append(f"({' OR '.join(terms)})")
                else:
                    query_parts.append(terms[0])
        
        # 用OR连接所有组
        return ' OR '.join(query_parts)
    
    @retry_multi(max_retries=3, delay=5)
    def _call_api(self, start_date, end_date, cursor=0):
        """调用medRxiv API获取论文数据
        
        参数:
            start_date (str): 开始日期，格式为YYYY-MM-DD
            end_date (str): 结束日期，格式为YYYY-MM-DD
            cursor (int): 分页游标
            
        返回:
            dict: API响应的JSON数据
        """
        url = self.api_papers_url.format(
            start_date=start_date,
            end_date=end_date,
            cursor=cursor
        )
        
        logger.info(f"调用medRxiv API: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning("API请求超时，将重试")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"解析JSON响应失败: {str(e)}")
            return None
    
    def _get_papers_from_api(self, start_date=None, end_date=None, limit=None):
        """从medRxiv API获取论文数据
        
        参数:
            start_date (str, optional): 开始日期，格式为YYYY-MM-DD
            end_date (str, optional): 结束日期，格式为YYYY-MM-DD
            limit (int, optional): 结果数量限制
            
        返回:
            list: 论文数据列表
        """
        if start_date is None:
            start_date = self._get_date_range()
        
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
            
        if limit is None:
            limit = MAX_RESULTS
        
        logger.info(f"从medRxiv API获取论文: 日期范围={start_date}至{end_date}, 限制={limit}")
        
        papers = []
        cursor = 0
        
        try:
            while len(papers) < limit:
                json_response = self._call_api(start_date, end_date, cursor)
                
                if not json_response or "messages" not in json_response or not json_response["messages"]:
                    logger.warning("API响应无效或没有消息")
                    break
                
                status = json_response["messages"][0].get("status")
                if status != "ok":
                    logger.warning(f"API响应状态不是'ok': {status}")
                    break
                
                count = json_response["messages"][0].get("count", 0)
                if count == 0:
                    logger.info("没有更多论文")
                    break
                
                # 更新游标位置
                cursor += count
                
                # 处理论文数据
                for paper_data in json_response.get("collection", []):
                    try:
                        paper = self._process_api_paper(paper_data)
                        if paper:
                            papers.append(paper)
                            logger.info(f"添加论文: {paper['title']} (发布日期: {paper['published']})")
                            
                            if len(papers) >= limit:
                                break
                    except Exception as e:
                        logger.error(f"处理API论文数据时出错: {str(e)}")
                        continue
            
            logger.info(f"从medRxiv API获取到 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"从medRxiv API获取论文时出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _process_api_paper(self, paper_data):
        """处理API返回的论文数据
        
        参数:
            paper_data (dict): API返回的单篇论文数据
            
        返回:
            dict: 处理后的论文数据
        """
        try:
            # 提取基本信息
            title = paper_data.get("title", "")
            if not title:
                return None
                
            doi = paper_data.get("doi", "")
            if not doi:
                import hashlib
                doi = f"10.1101/{hashlib.md5(title.encode()).hexdigest()}"
            
            # 处理作者信息
            authors = []
            author_data = paper_data.get("authors", "")
            if author_data:
                # 尝试解析作者字符串
                author_list = author_data.split(",")
                authors = [author.strip() for author in author_list if author.strip()]
            
            # 处理日期
            published = datetime.now().strftime("%Y-%m-%d")  # 默认为当前日期
            date_str = paper_data.get("date", "")
            if date_str:
                published = self._format_date(date_str)
            
            # 构建URL
            article_url = f"{self.base_url}/content/{doi}"
            pdf_url = f"{self.base_url}/content/{doi}.full.pdf"
            
            # 检查本地缓存
            paper_id = f"medrxiv_{doi.replace('/', '_').replace('.', '_')}"
            pdf_filename = f"{paper_id}.pdf"
            local_pdf_path = os.path.join(PDF_STORAGE_PATH, pdf_filename)
            has_local_cache = os.path.exists(local_pdf_path)
            
            # 构建论文数据
            return {
                'id': paper_id,
                'title': title,
                'authors': authors if authors else ["未知作者"],
                'abstract': paper_data.get("abstract", ""),
                'pdf_url': pdf_url,
                'published': published,
                'source': 'medrxiv',
                'categories': ["medRxiv Preprint"],
                'doi': doi,
                'article_url': article_url,
                'local_pdf_path': local_pdf_path if has_local_cache else None,
                'full_text': title + " " + paper_data.get("abstract", "")  # 用于关键词匹配
            }
            
        except Exception as e:
            logger.error(f"处理API论文数据时出错: {str(e)}")
            return None
    
    def fetch_papers(self):
        """获取符合条件的medRxiv论文
        
        返回:
            list: 论文数据列表
        """
        try:
            # 使用API方式获取论文
            start_date = self._get_date_range()
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"从medRxiv获取论文: {start_date} 至 {end_date}")
            papers = self._get_papers_from_api(start_date, end_date, MAX_RESULTS)
            
            if not papers or len(papers) == 0:
                logger.warning("未从medRxiv API获取到论文，尝试使用搜索方式")
                query = self._build_query_string(SEARCH_KEYWORDS)
                papers = self.search(query, start_date, MAX_RESULTS)
            
            # 应用关键词过滤
            original_count = len(papers)
            papers = filter_papers_by_keywords(papers, KEYWORD_FILTER)
            logger.info(f"从medRxiv获取到 {original_count} 篇论文，过滤后剩余 {len(papers)} 篇")
            return papers
            
        except Exception as e:
            logger.error(f"获取medRxiv论文时出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    @retry_multi(max_retries=3, delay=5)
    def search(self, query=None, from_date=None, limit=None):
        """搜索符合条件的论文（网页搜索方式）
        
        参数:
            query (str, optional): 搜索查询字符串，如果为None则使用配置中的关键词
            from_date (str, optional): 起始日期，格式为YYYY-MM-DD
            limit (int, optional): 结果数量限制
            
        返回:
            list: 论文数据列表
        """
        if query is None:
            query = self._build_query_string(SEARCH_KEYWORDS)
        
        if from_date is None:
            from_date = self._get_date_range()
            
        if limit is None:
            limit = MAX_