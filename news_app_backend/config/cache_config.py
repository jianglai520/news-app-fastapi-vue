import redis.asyncio as redis
from typing import Any
import json

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# 创建 Redis 的连接对象（配置 Redis 客户端）
redis_client = redis.Redis(
    host = REDIS_HOST,   # Redis 服务器主机地址
    port = REDIS_PORT,  # Redis 端口号
    db = REDIS_DB,   # Redis 数据库编号 0-15
    decode_responses = True,   # 是否将字节数据解码为字符串
    protocol = 2  # 强制使用 RESP2（解决客户端版本与 Redis 服务器版本不兼容）
)


# 设置缓存 和 读取缓存（字符串和 列表或者字典）

# 读取缓存：字符串
async def get_cache(key: str):
    # await redis_client.get(key)
    try:
        return await redis_client.get(key)
    except Exception as e:
        print(f"获取缓存失败:{e}")
        return None

# 读取缓存：列表或者字典
async def get_json_cache(key: str):
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)  # 序列化
        return None
    except Exception as e:
        print(f"获取json格式缓存失败:{e}")
        return None


# 设置缓存 setex(key, expire, value)
async def set_cache(key: str, value: Any, expire: int = 3600):  # expire = 3600 单位是秒 也就是一个小时
    try:
        if isinstance(value, (dict, list)):
            # 转字符串再存
            value = json.dumps(value, ensure_ascii = False)   # 中文正常保存
        await redis_client.setex(key, expire, value)
        return True
    except Exception as e:
        print(f"设置缓存失败:{e}")
        return False