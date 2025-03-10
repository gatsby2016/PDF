# 配置文件

# API密钥（替换OpenAI配置）
XUNFEI_APP_ID = "your xunfei spark appid"
XUNFEI_API_KEY = "your xunfei spark api key"
XUNFEI_API_SECRET = "your xunfei spark api secret"

# LLM配置
XUNFEI_DOMAIN = "4.0Ultra"
XUNFEI_URL = "wss://spark-api.xf-yun.com/v4.0/chat"  # API地址


# LLM提供商配置
LLM_PROVIDER = "openai"  # 可选: "openai", "zhipuai", "baidu"
LLM_MODEL = "gpt-4"

# 智谱AI配置
ZHIPUAI_API_KEY = "your-zhipuai-api-key"

# 百度文心一言配置
BAIDU_API_KEY = "your-baidu-api-key"
BAIDU_SECRET_KEY = "your-baidu-secret-key"

# 搜索配置
SEARCH_DOMAINS = ["cs.AI", "cs.CV"]  # arXiv领域 参考 https://arxiv.org/archive/cs

# 搜索关键词配置
SEARCH_KEYWORDS = [
    {
        "type": "AND",
        "keywords": ["pathology", "learning"]
    },
    {
        "type": "OR",
        "keywords": ["pathology", "histology"]
    }
]

# 搜索时间范围（天）
PAPER_SEARCH_DAYS = 3

# 每个来源最大结果数
MAX_RESULTS = 50

# PDF存储路径
PDF_STORAGE_PATH = "./papers"
SUMMARY_STORAGE_PATH = "./summaries"
SOCIAL_POST_PATH = "./social_posts"

# LLM配置
SUMMARY_MAX_TOKENS = 500
SOCIAL_POST_MAX_TOKENS = 300

# 社交媒体配置
ENABLE_TWITTER = False
TWITTER_API_KEY = ""
TWITTER_API_SECRET = ""
TWITTER_ACCESS_TOKEN = ""
TWITTER_ACCESS_SECRET = ""

# 运行频率 (小时)
UPDATE_FREQUENCY = 24
# 论文搜索时间范围（单位：天）
PAPER_SEARCH_DAYS = 3

# 是否在控制台显示图像预览
SHOW_IMAGE_PREVIEW = False


# 手动指定的PDF链接 - 只需提供URL，其他元数据将自动获取
MANUAL_PDF_LINKS = [
    "https://www.nature.com/articles/s41467-025-57283-x",
    "https://www.nature.com/articles/s41467-025-57072-6",
    # 可以添加更多PDF链接
]

# 关键词过滤配置
KEYWORD_FILTER = {
    # 是否启用关键词过滤
    "enabled": True,
    # 过滤模式: "include"(包含), "exclude"(排除), "both"(同时使用包含和排除)
    "mode": "both",
    # 包含关键词列表 - 论文必须包含这些关键词中的至少一个才会被保留
    "include_keywords": ["pathology", "histology", "microscopy", "biopsy", "tissue"],
    # 排除关键词列表 - 论文包含这些关键词中的任何一个将被排除
    "exclude_keywords": ["plant", "agriculture", "ecology"],
    # 匹配字段: "title"(仅标题), "abstract"(仅摘要), "all"(标题+摘要)
    "match_fields": "all",
    # 最小匹配分数 (0-100) - 用于相关性排序，分数越高表示越相关
    "min_score": 10
}