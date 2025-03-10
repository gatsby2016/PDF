import arxiv
import os
from datetime import datetime, timedelta
from config import SEARCH_DOMAINS, SEARCH_KEYWORDS, MAX_RESULTS, PAPER_SEARCH_DAYS, PDF_STORAGE_PATH, KEYWORD_FILTER
from utils.keyword_filter import filter_papers_by_keywords

class ArxivScraper:
    def __init__(self):
        self.client = arxiv.Client()
        self.search_domains = SEARCH_DOMAINS
        self.search_keywords = SEARCH_KEYWORDS
        self.max_results = MAX_RESULTS
    
    def fetch_papers(self):
        """获取符合条件的arXiv论文"""
        papers = []
        
        for domain in SEARCH_DOMAINS:
            for keyword_group in SEARCH_KEYWORDS:
                try:
                    # 构建查询
                    if keyword_group["type"] == "AND":
                        query = " AND ".join(keyword_group["keywords"])
                    else:  # OR
                        query = " OR ".join(keyword_group["keywords"])
                    
                    # 添加领域限制
                    query = f"cat:{domain} AND ({query})"
                    
                    # 添加时间限制
                    if PAPER_SEARCH_DAYS > 0:
                        from datetime import datetime, timedelta
                        date_limit = datetime.now() - timedelta(days=PAPER_SEARCH_DAYS)
                        date_str = date_limit.strftime("%Y%m%d")
                        query += f" AND submittedDate:[{date_str}000000 TO 99991231235959]"
                    
                    print(f"查询arXiv: {query}")
                    
                    # 执行查询
                    search = arxiv.Search(
                        query=query,
                        max_results=MAX_RESULTS,
                        sort_by=arxiv.SortCriterion.SubmittedDate,
                        sort_order=arxiv.SortOrder.Descending
                    )
                    
                    # 处理结果
                    for result in search.results():
                        # 检查是否已经添加过该论文
                        if any(p["id"] == result.get_short_id() for p in papers):
                            continue
                        
                        # 检查本地是否有缓存
                        from config import PDF_STORAGE_PATH
                        pdf_filename = f"{result.get_short_id()}.pdf"
                        local_pdf_path = os.path.join(PDF_STORAGE_PATH, pdf_filename)
                        
                        if os.path.exists(local_pdf_path):
                            print(f"发现arXiv论文的本地缓存: {local_pdf_path}")
                            has_local_cache = True
                        else:
                            has_local_cache = False
                        
                        # 构建论文数据
                        paper = {
                            "id": result.get_short_id(),
                            "title": result.title,
                            "authors": [author.name for author in result.authors],
                            "abstract": result.summary,
                            "pdf_url": result.pdf_url,
                            "published": result.published.strftime("%Y-%m-%d"),
                            "source": "arxiv",
                            "categories": [c.category for c in result.categories],
                            "local_pdf_path": local_pdf_path if has_local_cache else None
                        }
                        
                        papers.append(paper)
                        print(f"找到arXiv论文: {paper['title']}")
                    
                except Exception as e:
                    print(f"查询arXiv时出错: {str(e)}")
            
        return papers
    
    def __init__(self):
        self.client = arxiv.Client()
        self.search_domains = SEARCH_DOMAINS
        self.search_keywords = SEARCH_KEYWORDS
        self.max_results = MAX_RESULTS
    
    def fetch_papers(self):
        """获取arXiv上的最新论文"""
        # 构建查询字符串
        domain_query = " OR ".join([f"cat:{domain}" for domain in self.search_domains])
        
        # 构建复杂的关键词查询 - 支持多种组合形式
        keyword_queries = []
        for keyword_group in self.search_keywords:
            if isinstance(keyword_group, dict):
                # 处理字典形式的关键词组合配置
                combo_type = keyword_group.get('type', 'OR')
                keywords = keyword_group.get('keywords', [])
                
                # 跳过空关键词列表
                if not keywords:
                    continue
                    
                if combo_type == 'AND':
                    # 所有关键词都必须出现
                    and_query = " AND ".join([f"\"{keyword}\"" for keyword in keywords])
                    keyword_queries.append(f"({and_query})")
                elif combo_type == 'OR':
                    # 任意关键词出现即可
                    or_query = " OR ".join([f"\"{keyword}\"" for keyword in keywords])
                    keyword_queries.append(f"({or_query})")
                elif combo_type == 'ADJACENT':
                    # 关键词必须相邻出现
                    if len(keywords) >= 2:  # 至少需要两个关键词才能使用ADJACENT
                        adj_query = " NEAR ".join([f"\"{keyword}\"" for keyword in keywords])
                        keyword_queries.append(f"({adj_query})")
                elif combo_type == 'NOT':
                    # 包含第一个关键词但不包含其他关键词
                    if len(keywords) >= 2:  # 至少需要两个关键词才能使用NOT
                        not_query = f"\"{keywords[0]}\""
                        for keyword in keywords[1:]:
                            not_query += f" AND NOT \"{keyword}\""
                        keyword_queries.append(f"({not_query})")
            elif isinstance(keyword_group, list):
                # 向后兼容：列表形式默认为AND组合
                if keyword_group:  # 跳过空列表
                    and_query = " AND ".join([f"\"{keyword}\"" for keyword in keyword_group])
                    keyword_queries.append(f"({and_query})")
            else:
                # 单个关键词
                keyword_queries.append(f"\"{keyword_group}\"")
        
        # 将所有关键词组合以OR连接
        if keyword_queries:
            keyword_query = " OR ".join(keyword_queries)
        else:
            # 如果没有有效的关键词查询，使用通配符
            keyword_query = "\"*\""
        
        # 从配置文件获取时间范围
        date_since = datetime.now() - timedelta(days=PAPER_SEARCH_DAYS)
        date_query = f"submittedDate:[{date_since.strftime('%Y%m%d')}000000 TO 99991231235959]"
        
        # 完整查询
        query = f"({domain_query}) AND ({keyword_query}) AND {date_query}"
        
        print(f"执行查询: {query}")  # 打印查询字符串，便于调试
        
        try:
            # 执行查询
            search = arxiv.Search(
                query=query,
                max_results=self.max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            # 处理结果
            papers = []
            try:
                # 使用 arxiv.Client 来获取结果
                client = arxiv.Client()
                for result in client.results(search):
                    paper = {
                        'id': result.entry_id,
                        'title': result.title,
                        'authors': [author.name for author in result.authors],
                        'abstract': result.summary,
                        'pdf_url': result.pdf_url,
                        'published': result.published,
                        'source': 'arxiv',
                        'categories': result.categories
                    }
                    papers.append(paper)
            except Exception as e:
                print(f"处理搜索结果时出错: {str(e)}")
                # 尝试备用方法
                try:
                    print("尝试使用备用方法获取结果...")
                    # 直接使用 arxiv.Search.get 方法
                    results = list(arxiv.Search(
                        query=query,
                        max_results=self.max_results,
                        sort_by=arxiv.SortCriterion.SubmittedDate
                    ).get())
                    
                    for result in results:
                        paper = {
                            'id': result.entry_id,
                            'title': result.title,
                            'authors': [author.name for author in result.authors],
                            'abstract': result.summary,
                            'pdf_url': result.pdf_url,
                            'published': result.published,
                            'source': 'arxiv',
                            'categories': result.categories
                        }
                        # 添加full_text字段用于关键词匹配
                        paper['full_text'] = paper['title'] + " " + paper['abstract']
                        papers.append(paper)
                except Exception as e2:
                    print(f"备用方法也失败: {str(e2)}")
            
            # 应用关键词过滤
            original_count = len(papers)
            papers = filter_papers_by_keywords(papers, KEYWORD_FILTER)
            print(f"从arXiv获取到 {original_count} 篇论文，过滤后剩余 {len(papers)} 篇")
            return papers
            
        except Exception as e:
            print(f"执行arXiv搜索时出错: {str(e)}")
            return []