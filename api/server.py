"""FastAPI服务器

主要的API服务器实现
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_server_config
from .routes import register_routes
from .middleware import setup_middleware
from .websocket import setup_websocket

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的初始化
    logger.info("正在启动 LangChain MindSearch API 服务器...")
    
    # 这里可以添加启动时的初始化逻辑
    # 例如：数据库连接、缓存初始化等
    
    yield
    
    # 关闭时的清理
    logger.info("正在关闭 LangChain MindSearch API 服务器...")
    
    # 这里可以添加关闭时的清理逻辑
    # 例如：关闭数据库连接、清理缓存等


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    # 获取服务器配置
    config = get_server_config()
    
    # 创建FastAPI应用
    app = FastAPI(
        title="LangChain MindSearch API",
        description="基于LangChain重构的MindSearch智能搜索系统",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加Gzip压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 设置自定义中间件
    setup_middleware(app)
    
    # 注册路由
    register_routes(app)
    
    # 设置WebSocket
    setup_websocket(app)
    
    # 全局异常处理器
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "type": "http_error"
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "内部服务器错误",
                    "type": "internal_error"
                }
            }
        )
    
    # 健康检查端点
    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "service": "langchain-mindsearch",
            "version": "1.0.0"
        }
    
    # 根路径
    @app.get("/")
    async def root() -> Dict[str, str]:
        """根路径"""
        return {
            "message": "欢迎使用 LangChain MindSearch API",
            "docs": "/docs",
            "health": "/health"
        }
    
    return app


def run_server(host: str = None, port: int = None, reload: bool = False):
    """运行服务器"""
    config = get_server_config()
    
    # 使用传入的参数或配置文件的值
    host = host or config.host
    port = port or config.port
    
    logger.info(f"启动服务器: http://{host}:{port}")
    
    uvicorn.run(
        "langchain_rebuild.api.server:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_server(reload=True)