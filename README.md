# 📚 学术论文自动爬取与分析系统PDF (Preprint Digestion Framework) 🧠

## 一个基于Trae AI 编辑器的、代码生成的、实验性的、自动化文献简短综述工具🔬

### **✨ 本设计目的在于 ✨**

> 🚀 一方面，基于代码生成工具 **Trae AI 编辑器**实现脑海中一些稀奇古怪的新想法，快速验证；
>
> 📊 另一方面，也是受到[翔哥减论 @减论(Reduct) bilibili](https://space.bilibili.com/3493104581610312?spm_id_from=333.337.0.0)的启发，把文献内容往熵减方向压缩，因此实现特定领域的自动文献简洁综述工具，可以快速生成简短综述总结，加快促进学术研究的传播，也帮助大家高效追踪最新研究。

### 💡 做科研，就得保持 `daily充电，24h待机` ⚡

**最近我也尝试更新一点每日文献订阅简报精选，欢迎大家去小红书一起交流 [@起舞的跳跳虫](https://www.xiaohongshu.com/user/profile/62b540c0000000001b02ab4d)** 🤝

-------

## 项目简介

本项目是一个自动化工具，用于从多个学术预印本平台（如 bioRxiv、medRxiv 等）爬取最新的学术论文，并根据关键词进行筛选、下载和分析。该系统特别适合研究人员和学者用于追踪特定领域（如病理学与AI结合）的最新研究进展。

## 功能特点

- 🔍 **多平台爬取**：支持从 bioRxiv、medRxiv 等多个预印本平台爬取论文
- 🔎 **灵活的关键词搜索**：支持 AND/OR 逻辑组合的关键词搜索（如"pathology AND AI"或"digital pathology OR computational pathology"）
- 📅 **时间范围筛选**：可设置搜索特定时间范围内发布的论文（默认为最近30天）
- 📥 **自动下载 PDF**：自动下载符合条件的论文 PDF 文件到本地存储
- 📊 **数据结构化存储**：将爬取的论文信息以结构化方式存储，包括标题、作者、摘要、DOI等
- 🤖 **LLM论文总结**：利用大语言模型自动生成论文摘要和社交媒体分享内容
- 📝 **详细日志记录**：记录爬取过程中的各种信息，方便调试和追踪问题

## 系统架构

本系统主要由以下几个部分组成：

1. **爬虫模块**：负责从各个预印本平台爬取论文信息
   - `biorxiv_scraper.py`：bioRxiv平台爬虫
   - `medrxiv_scraper.py`：medRxiv平台爬虫

2. **配置模块**：集中管理系统配置
   - `config.py`：包含搜索关键词、时间范围、结果数量限制等配置

3. **下载模块**：负责下载论文PDF文件
   - 支持断点续传和重试机制

4. **分析模块**：对爬取的论文进行分析和处理
   - 关键词匹配和筛选
   - 文本提取和处理

5. **LLM总结模块**：使用大语言模型生成论文摘要和社交媒体内容
   - 支持LLM提供商（目前支持国内讯飞星火等）
   - 自定义提示词模板，生成高质量摘要

## LLM论文总结功能

本系统集成了多种大语言模型(LLM)，用于自动生成论文摘要和社交媒体分享内容。这一功能可以帮助研究人员快速了解论文的核心内容，而无需首先阅读全文。

### 支持的LLM提供商

- **讯飞星火** (默认): 使用讯飞星火大模型4.0Ultra版本进行论文总结

### 总结功能特点

- **自动摘要生成**: 从PDF全文中提取关键信息，生成简洁明了的摘要
- **社交媒体内容创建**: 自动生成适合在社媒等平台分享的简短内容
- **可定制提示词**: 可以根据需要调整提示词模板，生成不同风格和侧重点的摘要
- **多语言支持**: 支持中英文等多种语言的摘要生成
- **批量处理**: 可以批量处理多篇论文，提高效率

### 配置LLM

在`config.py`文件中可以配置LLM相关参数：

```python
# LLM提供商配置
LLM_PROVIDER = "xunfei"  # 可选: "xunfei", "openai", "zhipuai", "baidu"

# 讯飞星火配置
XUNFEI_APP_ID = "your xunfei spark appid"
XUNFEI_API_KEY = "your xunfei spark api key"
XUNFEI_API_SECRET = "your xunfei spark api secret"
XUNFEI_DOMAIN = "4.0Ultra"
XUNFEI_URL = "wss://spark-api.xf-yun.com/v4.0/chat"

# 摘要和社交媒体内容长度配置
SUMMARY_MAX_TOKENS = 500
SOCIAL_POST_MAX_TOKENS = 300
```

### 使用示例
系统会自动为下载的论文生成摘要，并存储在配置的摘要目录中：

```plaintext
📁 summaries/
   └── 📄 biorxiv_xxxx.txt  # 论文摘要文件
   └── 📄 medrxiv_xxxx.txt  # 论文摘要文件
```

同时，系统还会生成适合社交媒体分享的简短内容：

```plaintext
📁 social_posts/
   └── 📄 biorxiv_xxxx.json  # 社交媒体内容
   └── 📄 medrxiv_xxxx.json  # 社交媒体内容
```

## 系统要求

- Python 3.7+
- 依赖库：
  - requests：用于发送HTTP请求
  - beautifulsoup4：用于解析HTML
  - datetime：用于日期处理
  - logging：用于日志记录
  - re：用于正则表达式匹配
  - websocket-client：用于与讯飞星火API通信

## 安装方法

1. 克隆仓库到本地：

```bash
git clone https://github.com/gatsby2016/PDF.git
cd PDF
```

2. 安装依赖：

```bash
pip install requests beautifulsoup4 websocket-client
```

## 配置说明
在 config.py 文件中可以进行以下配置：

```python
# 搜索关键词配置
SEARCH_KEYWORDS = [
    {
        "type": "AND",
        "keywords": ["pathology", "AI"]
    },
    {
        "type": "OR",
        "keywords": ["digital pathology", "computational pathology"]
    }
]

# 搜索时间范围（天）
PAPER_SEARCH_DAYS = 30

# 每个来源最大结果数
MAX_RESULTS = 50

# PDF存储路径
PDF_STORAGE_PATH = "papers"
```

### 关键词配置说明

- AND类型 ：要求论文同时包含所有指定的关键词

- OR类型 ：要求论文包含任一指定的关键词

- 多个关键词组之间是OR关系，即满足任一组的条件即可


## 使用方法

### 基本使用

1. 运行主程序以爬取论文：
```bash
python main.py
```

2. 查看爬取结果：

   - 论文信息将输出到控制台
   - PDF文件将下载到配置的存储路径中
   - 摘要和社交媒体内容将生成到对应目录

### 爬虫模块单独使用

您也可以单独使用爬虫模块：

```python
from scrapers.biorxiv_scraper import BiorxivScraper

# 创建爬虫实例
scraper = BiorxivScraper()

# 获取论文
papers = scraper.fetch_papers()

# 打印结果
for paper in papers:
    print(f"标题: {paper['title']}")
    print(f"作者: {', '.join(paper['authors'])}")
    print(f"摘要: {paper['abstract'][:200]}...")
    print(f"DOI: {paper['doi']}")
    print(f"PDF: {paper['pdf_url']}")
    print("-" * 50)
```

## 爬虫实现细节

### bioRxiv爬虫

bioRxiv爬虫实现了以下功能：

1. 构建查询字符串 ：支持复杂的AND/OR逻辑组合

2. 日期格式化 ：处理多种日期格式

3. 健壮的HTML解析 ：使用多种选择器确保能够适应网站结构变化

4. 错误处理 ：详细的日志记录和异常处理

5. 本地缓存检查 ：避免重复下载已有PDF

关键代码示例：

```python
def _build_query(self, keywords):
    """构建bioRxiv查询字符串"""
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
```

### medRxiv爬虫

medRxiv爬虫与bioRxiv爬虫类似，但针对medRxiv网站的特定结构进行了适配。

## 注意事项

- 请遵守各学术平台的使用条款和爬虫政策

- 建议设置合理的爬取频率，避免对服务器造成过大负担

- PDF文件可能较大，请确保有足够的存储空间

- 网站结构可能会变化，如遇到爬取失败，请查看日志并更新相应的CSS选择器

- 使用LLM功能需要配置相应的API密钥，请确保已正确设置

## 常见问题

Q: 为什么某些论文无法下载PDF？   
A: 可能是因为该论文需要付费访问，或者网络连接问题，或者DOI解析错误。

Q: 如何修改搜索的关键词？   
A: 在 config.py 文件中修改 SEARCH_KEYWORDS 配置。

Q: 爬虫报错"未找到搜索结果容器"怎么办？   
A: 网站结构可能已更新，请查看保存的HTML文件并更新相应的CSS选择器。

Q: 如何更换使用的LLM模型？    
A: 在 config.py 中修改 LLM_PROVIDER 和相应的API配置，目前仅支持openai和讯飞星火。

## 未来计划

- ~~实现LLM自动生成论文摘要功能~~

- 添加更多预印本平台支持

- 实现定时爬取和邮件通知功能

- 添加Web界面，方便用户操作

- 添加论文相似度分析，发现研究趋势

- 支持更多LLM提供商和模型

## 贡献指南

欢迎提交Pull Request或Issue来帮助改进这个项目！

## 致谢
感谢 [Trae AI 编辑器](
https://www.trae.ai/
) 为这个项目提供了强大的代码生成能力。

感谢翔哥对这个项目的支持和认可，让这个项目更加深入，欢迎大家关注[**减论科技@bilibili**](https://space.bilibili.com/3493104581610312?spm_id_from=333.337.0.0) [**减论科技@小红书**](https://www.xiaohongshu.com/user/profile/5df112140000000001009dcf)！减论，减法论（Reduct Theory），用科技链接个体!

## 许可证

本项目采用MIT许可证。