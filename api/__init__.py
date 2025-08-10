"""API模块

提供RESTful接口
"""

from .server import create_app, run_server
from .routes import register_routes
from .middleware import setup_middleware
from .websocket import setup_websocket

__all__ = [
    'create_app',
    'run_server', 
    'register_routes',
    'setup_middleware',
    'setup_websocket'
]