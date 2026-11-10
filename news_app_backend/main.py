from fastapi import FastAPI
from routers import news
from contextlib import asynccontextmanager
from config.db_config import async_engine, close_db
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：探一次库，连不上就立刻启动失败，而不是等到第一个请求才报错
    async with async_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    yield

    # 关闭时：释放连接池
    await close_db()


app = FastAPI(title="新闻资讯 API", version="0.1.0", lifespan=lifespan)


@app.get("/")
async def get_news():
    return {"msg": "this is a news_app_fastapi_vue"}


# 挂载路由/注册路由
app.include_router(news.router)