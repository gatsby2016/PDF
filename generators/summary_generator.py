import os
import json
from datetime import datetime
from config import SUMMARY_STORAGE_PATH, SUMMARY_MAX_TOKENS
from processors.llm_processor import LLMProcessor

class SummaryGenerator:
    def __init__(self):
        self.storage_path = SUMMARY_STORAGE_PATH
        self.llm_processor = LLMProcessor()
        self.max_tokens = SUMMARY_MAX_TOKENS
    
    def evaluate_paper_value(self, paper):
        """评估论文的潜在研究价值和学术影响力"""
        prompt = f"""
请评估以下学术论文的潜在研究价值和学术影响力：

标题: {paper['title']}
作者: {', '.join(paper['authors'])}
发表日期: {paper['published']}
来源: {paper['source']}
分类: {', '.join(paper['categories'])}

摘要:
{paper['abstract']}

请从以下几个方面进行评估，并给出一个总体评分（1-10分）：
1. 研究问题的重要性和创新性
2. 研究方法的科学性和严谨性
3. 研究结果的可靠性和影响力
4. 与当前研究热点的相关性

最后，请明确给出"有价值"或"价值有限"的结论，以及简短理由（不超过50字）。
"""
        
        # 使用LLM评估论文价值
        evaluation = self.llm_processor.process_text(prompt, self.max_tokens)
        
        # 解析评估结果
        is_valuable = False
        if "有价值" in evaluation and "价值有限" not in evaluation:
            is_valuable = True
        elif "价值有限" in evaluation:
            is_valuable = False
        else:
            # 如果没有明确结论，查找评分
            import re
            score_match = re.search(r'(\d+)[\s\/]10', evaluation)
            if score_match:
                score = int(score_match.group(1))
                is_valuable = score >= 6  # 6分及以上认为有价值
            else:
                # 默认为有价值，避免错过重要论文
                is_valuable = True
        
        return {
            'is_valuable': is_valuable,
            'evaluation': evaluation
        }
    
    def generate_summary(self, paper, pdf_content):
        """生成论文综述"""
        # 检查是否存在缓存的摘要文件
        paper_id = paper['id'].split('/')[-1] if '/' in paper['id'] else paper['id']
        cache_file = f"{paper_id.replace('.', '_').replace(':', '_')}_summary.json"
        cache_path = os.path.join(self.storage_path, cache_file)
        
        # 如果存在缓存文件，直接读取返回
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    return cache_data['summary']
            except Exception as e:
                print(f"读取缓存文件失败: {str(e)}")
                # 如果读取缓存失败，继续生成新的摘要
        
        # 首先评估论文价值
        evaluation_result = self.evaluate_paper_value(paper)
        
        # 如果论文价值有限，返回None表示不需要继续处理
        if not evaluation_result['is_valuable']:
            print(f"论文 '{paper['title']}' 评估为价值有限，跳过摘要生成。")
            print(f"评估结果: {evaluation_result['evaluation']}")
            
            # 保存评估结果
            file_name = f"{paper_id.replace('.', '_').replace(':', '_')}_evaluation.json"
            file_path = os.path.join(self.storage_path, file_name)
            
            paper_copy = paper.copy()
            for key, value in paper_copy.items():
                if isinstance(value, datetime):
                    paper_copy[key] = value.isoformat()
            
            evaluation_data = {
                'paper': paper_copy,
                'evaluation': evaluation_result['evaluation'],
                'is_valuable': evaluation_result['is_valuable'],
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation_data, f, ensure_ascii=False, indent=2)
                
            return None
        
        # 以下是原有的摘要生成逻辑
        prompt = f"""
请对以下学术论文进行简短综述（500字以内）：

标题: {paper['title']}
作者: {', '.join(paper['authors'])}
发表日期: {paper['published']}
来源: {paper['source']}
分类: {', '.join(paper['categories'])}

摘要:
{paper['abstract']}

论文内容:
{pdf_content[:5000]}...

请提供以下内容:
1. 研究背景和问题（1-2句话）
2. 主要方法和创新点（2-3句话）
3. 关键发现和结果（2-3句话）
4. 研究意义和潜在影响（1-2句话）

请使用学术但通俗易懂的语言，避免过于技术性的术语，以便非专业人士也能理解。
"""
        
        # 使用LLM生成综述
        summary = self.llm_processor.process_text(prompt, self.max_tokens)
        
        # 保存综述
        file_name = f"{paper_id.replace('.', '_').replace(':', '_')}_summary.json"
        file_path = os.path.join(self.storage_path, file_name)
        
        # Create a copy of the paper dict to avoid modifying the original
        paper_copy = paper.copy()
        
        # Convert datetime objects to strings
        for key, value in paper_copy.items():
            if isinstance(value, datetime):
                paper_copy[key] = value.isoformat()
        
        summary_data = {
            'paper': paper_copy,
            'summary': summary,
            'evaluation': evaluation_result['evaluation'],
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        return summary