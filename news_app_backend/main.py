from fastapi import FastAPI
from routers import news

app = FastAPI()

@app.get("/")
async def get_news():
    return {"msg": "this is a news_app_fastapi_vue"}


# 挂载路由/注册路由
app.include_router(news.router)