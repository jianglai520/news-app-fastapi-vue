from fastapi import APIRouter

# 创建 APIRouter 实例
# prefix 路由前缀（API 接口文档规范）
# tags 分组 标签
router = APIRouter(prefix = "/api/news", tags = ["news"])

@router.get("/categories")
async def get_categories():
    return {"msg": "获取分类成功"}