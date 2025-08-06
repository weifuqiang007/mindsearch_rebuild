"""API中间件

提供请求处理、日志记录、错误处理等功能
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
import json

# 配置日志
logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        logger.info(
            f"请求开始 - ID: {request_id}, 方法: {request.method}, "
            f"路径: {request.url.path}, 客户端: {request.client.host if request.client else 'unknown'}"
        )
        
        # 将请求ID添加到请求状态
        request.state.request_id = request_id
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                f"请求完成 - ID: {request_id}, 状态码: {response.status_code}, "
                f"处理时间: {process_time:.3f}s"
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录错误
            logger.error(
                f"请求失败 - ID: {request_id}, 错误: {str(e)}, "
                f"处理时间: {process_time:.3f}s",
                exc_info=True
            )
            
            # 重新抛出异常
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.client_requests = {}  # 存储客户端请求记录
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 获取当前时间
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup_expired_records(current_time)
        
        # 检查速率限制
        if self._is_rate_limited(client_ip, current_time):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁，请稍后再试"
            )
        
        # 记录请求
        self._record_request(client_ip, current_time)
        
        # 处理请求
        response = await call_next(request)
        
        # 添加速率限制头
        remaining = self._get_remaining_requests(client_ip, current_time)
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        return response
    
    def _cleanup_expired_records(self, current_time: float):
        """清理过期记录"""
        cutoff_time = current_time - 60  # 1分钟前
        
        for client_ip in list(self.client_requests.keys()):
            self.client_requests[client_ip] = [
                timestamp for timestamp in self.client_requests[client_ip]
                if timestamp > cutoff_time
            ]
            
            # 如果没有记录，删除客户端
            if not self.client_requests[client_ip]:
                del self.client_requests[client_ip]
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """检查是否超过速率限制"""
        if client_ip not in self.client_requests:
            return False
        
        # 计算最近一分钟的请求数
        cutoff_time = current_time - 60
        recent_requests = [
            timestamp for timestamp in self.client_requests[client_ip]
            if timestamp > cutoff_time
        ]
        
        return len(recent_requests) >= self.calls_per_minute
    
    def _record_request(self, client_ip: str, current_time: float):
        """记录请求"""
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = []
        
        self.client_requests[client_ip].append(current_time)
    
    def _get_remaining_requests(self, client_ip: str, current_time: float) -> int:
        """获取剩余请求数"""
        if client_ip not in self.client_requests:
            return self.calls_per_minute
        
        cutoff_time = current_time - 60
        recent_requests = [
            timestamp for timestamp in self.client_requests[client_ip]
            if timestamp > cutoff_time
        ]
        
        return max(0, self.calls_per_minute - len(recent_requests))


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 处理请求
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """请求大小限制中间件"""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 默认10MB
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 检查Content-Length头
        content_length = request.headers.get("content-length")
        
        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=413,
                    detail=f"请求体过大，最大允许 {self.max_size} 字节"
                )
        
        return await call_next(request)


class ResponseCompressionMiddleware(BaseHTTPMiddleware):
    """响应压缩中间件"""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # 检查是否支持压缩
        accept_encoding = request.headers.get("accept-encoding", "")
        
        if "gzip" in accept_encoding and response.status_code == 200:
            # 对于JSON响应，添加压缩提示
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                response.headers["Vary"] = "Accept-Encoding"
        
        return response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """缓存控制中间件"""
    
    def __init__(self, app, default_max_age: int = 300):  # 默认5分钟
        super().__init__(app)
        self.default_max_age = default_max_age
        
        # 定义不同路径的缓存策略
        self.cache_policies = {
            "/api/v1/config": 3600,  # 配置信息缓存1小时
            "/api/v1/status": 60,    # 状态信息缓存1分钟
            "/health": 30,           # 健康检查缓存30秒
        }
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # 只对GET请求设置缓存
        if request.method == "GET" and response.status_code == 200:
            path = request.url.path
            
            # 查找匹配的缓存策略
            max_age = self.default_max_age
            for cache_path, cache_time in self.cache_policies.items():
                if path.startswith(cache_path):
                    max_age = cache_time
                    break
            
            # 设置缓存头
            response.headers["Cache-Control"] = f"public, max-age={max_age}"
            response.headers["ETag"] = f'"langchain-mindsearch-{hash(str(response.body))}"'
        
        return response


def setup_middleware(app: FastAPI):
    """设置所有中间件"""
    
    # 添加请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # 添加速率限制中间件（每分钟60次请求）
    app.add_middleware(RateLimitMiddleware, calls_per_minute=60)
    
    # 添加安全中间件
    app.add_middleware(SecurityMiddleware)
    
    # 添加请求大小限制中间件（10MB）
    app.add_middleware(RequestSizeMiddleware, max_size=10 * 1024 * 1024)
    
    # 添加响应压缩中间件
    app.add_middleware(ResponseCompressionMiddleware)
    
    # 添加缓存控制中间件
    app.add_middleware(CacheControlMiddleware, default_max_age=300)
    
    logger.info("所有中间件已设置完成")