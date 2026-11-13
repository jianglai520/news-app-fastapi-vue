"""
新闻相关的缓存方法：新闻分类的读取和写入
key: value形式
"""
from config.cache_config import get_json_cache, set_cache
from typing import List, Any, Dict, Optional

CATEGORIES_KEY = "news:categories"
NEWS_LIST_PREFIX = "news_list"

# 获取新闻分类缓存
async def get_cached_categories():
    return await get_json_cache(CATEGORIES_KEY)

# 写入新闻分类缓存: 缓存的数据、过期的时间
# 分类、配置：7200
# 列表： 600
# 详情：1800
# 验证码：120
# 原则：数据越稳定，缓存越持久
# 避免所有 key 同时过期，引起缓存雪崩（注意，不同的数据要设置不同的过期时间）
async def set_cached_categories(data: List[Dict[str, Any]], expire: int = 7200):
    return await set_cache(CATEGORIES_KEY, data, expire)

# 写入缓存-新闻列表 key = news_list:分类id:页码:每页数量  + 列表数据 + 过期时间
async def set_cache_news_list(category_id: Optional[int], page: int, page_size: int, news_list: List[Dict[str, Any]], expire: int = 1800):
    # 调用封装的的 Redis 的设置方法，存新闻列表缓存
    category_part = category_id if category_id is not None else "all"
    key = f"{NEWS_LIST_PREFIX}{category_part}:{page}:{page_size}"
    return await set_cache(key, news_list, expire)

# 读取缓存-新闻列表
async def get_cache_news_list(category_id: Optional[int], page: int, page_size: int):
    category_part = category_id if category_id is not None else "all"
    key = f"{NEWS_LIST_PREFIX}{category_part}:{page}:{page_size}"
    return await get_json_cache(key)