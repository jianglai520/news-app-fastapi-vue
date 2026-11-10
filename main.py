from fastapi import FastAPI

app = FastAPI()

@app.get("/news")
async def get_news():
    return {"msg": "this is an news"}