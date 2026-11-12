from fastapi import Header, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_db
from crud import users
from starlette import status

# 根据 Token 查询用户，最后返回用户
async def get_current_user(
        authorization: str = Header(..., alias = "Authorization"),
        db: AsyncSession = Depends(get_db)
):
    # users.get_user_by_token()
    token = authorization.replace("Bearer ", "")
    user = await users.get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "无效的令牌或已经过期的令牌")

    return user