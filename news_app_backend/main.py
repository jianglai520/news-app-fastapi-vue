from fastapi import FastAPI
from routers import news, users
from contextlib import asynccontextmanager
from config.db_config import async_engine, close_db
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：探一次库，连不上就立刻启动失败，而不是等到第一个请求才报错
    async with async_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    yield

    # 关闭时：释放连接池
    await close_db()


app = FastAPI(title="新闻资讯 API", version="0.1.0", lifespan=lifespan)

# 解决跨域资源共享（CORS）
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],   # 允许的源，开发当中允许所有源，生产环境务必指定源
    allow_credentials = True,   # 允许携带 Cookie
    allow_methods = ["*"],  # 允许的请求方法
    allow_headers = ["*"]   # 允许的请求头
)


@app.get("/")
async def get_news():
    return {"msg": "this is a news_app_fastapi_vue"}


# 挂载路由/注册路由
app.include_router(news.router)
app.include_router(users.router)