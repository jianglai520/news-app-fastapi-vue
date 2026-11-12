from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Any

def success_response(message: str = "success", data: Any = None):
    content = {
        "code": 200,
        "message": message,
        "data": data
    }

    # 目标：任何的 FastAPI Pydantic ORM 对象都要正常响应 -> code  message  data
    return JSONResponse(content = jsonable_encoder(content))