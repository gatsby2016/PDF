import logging
import re

logger = logging.getLogger(__name__)

def filter_papers_by_keywords(papers, filter_config):
    """
    根据关键词配置过滤论文列表
    
    参数:
        papers (list): 论文数据列表
        filter_config (dict): 关键词过滤配置
        
    返回:
        list: 过滤后的论文列表
    """
    # 如果过滤功能未启用，直接返回原始列表
    if not filter_config.get("enabled", False):
        return papers
    
    filtered_papers = []
    mode = filter_config.get("mode", "both")
    include_keywords = filter_config.get("include_keywords", [])
    exclude_keywords = filter_config.get("exclude_keywords", [])
    match_fields = filter_config.get("match_fields", "all")
    min_score = filter_config.get("min_score", 0)
    
    logger.info(f"使用关键词过滤论文: 模式={mode}, 包含关键词={include_keywords}, 排除关键词={exclude_keywords}")
    
    for paper in papers:
        # 确定要匹配的文本
        if match_fields == "title":
            text_to_match = paper.get("title", "")
        elif match_fields == "abstract":
            text_to_match = paper.get("abstract", "")
        else:  # "all"
            text_to_match = paper.get("full_text", "") or (paper.get("title", "") + " " + paper.get("abstract", ""))
        
        # 转换为小写进行不区分大小写的匹配
        text_to_match = text_to_match.lower()
        
        # 计算匹配分数
        score = 0
        matched_keywords = []
        excluded = False
        
        # 检查包含关键词
        if mode in ["include", "both"]:
            for keyword in include_keywords:
                if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', text_to_match):
                    score += 10  # 每匹配一个关键词增加10分
                    matched_keywords.append(keyword)
        
        # 检查排除关键词
        if mode in ["exclude", "both"]:
            for keyword in exclude_keywords:
                if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', text_to_match):
                    excluded = True
                    logger.info(f"论文被排除: {paper.get('title', '')} (包含排除关键词: {keyword})")
                    break
        
        # 根据模式决定是否保留论文
        keep_paper = False
        if mode == "include":
            keep_paper = score >= min_score
        elif mode == "exclude":
            keep_paper = not excluded
        else:  # "both"
            keep_paper = (score >= min_score) and (not excluded)
        
        if keep_paper:
            # 添加匹配分数和匹配的关键词到论文数据中
            paper["keyword_match_score"] = score
            paper["matched_keywords"] = matched_keywords
            filtered_papers.append(paper)
            logger.info(f"保留论文: {paper.get('title', '')} (匹配分数: {score}, 匹配关键词: {matched_keywords})")
        else:
            logger.info(f"过滤掉论文: {paper.get('title', '')} (匹配分数: {score}, 最小要求: {min_score})")
    
    # 按匹配分数排序（可选）
    filtered_papers.sort(key=lambda x: x.get("keyword_match_score", 0), reverse=True)
    
    logger.info(f"关键词过滤前: {len(papers)} 篇论文, 过滤后: {len(filtered_papers)} 篇论文")
    return filtered_papers