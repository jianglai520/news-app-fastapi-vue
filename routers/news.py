from fastapi import APIRouter

# 创建 APIRouter 实例
router = APIRouter(prefix = "/api/news", tags = ["news"])