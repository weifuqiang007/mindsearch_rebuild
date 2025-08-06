"""WebSocket支持

提供实时通信功能
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from pydantic import BaseModel, ValidationError

from ..agents.mindsearch_agent import AsyncMindSearchAgent
from ..agents.react_agent import ReactAgent
from ..agents.search_agent import SearchAgent, SearchStrategy
from ..core.llm_manager import LLMProvider
from ..core.search_tools import SearchEngine

# 配置日志
logger = logging.getLogger(__name__)

# WebSocket消息模型
class WebSocketMessage(BaseModel):
    """WebSocket消息"""
    type: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None
    session_id: Optional[str] = None

class WebSocketResponse(BaseModel):
    """WebSocket响应"""
    type: str
    data: Dict[str, Any]
    timestamp: str
    session_id: str
    status: str = "success"
    error: Optional[str] = None

# 连接管理器
class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_agents: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """接受连接"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # 初始化会话智能体
        self.session_agents[session_id] = {
            "mindsearch": AsyncMindSearchAgent(),
            "react": ReactAgent(),
            "search": SearchAgent()
        }
        
        logger.info(f"WebSocket连接已建立: {session_id}")
        
        # 发送连接确认
        await self.send_message(session_id, {
            "type": "connection_established",
            "data": {
                "session_id": session_id,
                "message": "连接已建立",
                "available_agents": ["mindsearch", "react", "search"]
            }
        })
    
    def disconnect(self, session_id: str):
        """断开连接"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        if session_id in self.session_agents:
            del self.session_agents[session_id]
        
        logger.info(f"WebSocket连接已断开: {session_id}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """发送消息"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            
            if websocket.client_state == WebSocketState.CONNECTED:
                response = WebSocketResponse(
                    type=message["type"],
                    data=message["data"],
                    timestamp=datetime.now().isoformat(),
                    session_id=session_id
                )
                
                try:
                    await websocket.send_text(response.model_dump_json())
                except Exception as e:
                    logger.error(f"发送消息失败: {e}")
                    self.disconnect(session_id)
    
    async def send_error(self, session_id: str, error_message: str, error_type: str = "error"):
        """发送错误消息"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            
            if websocket.client_state == WebSocketState.CONNECTED:
                response = WebSocketResponse(
                    type=error_type,
                    data={"message": error_message},
                    timestamp=datetime.now().isoformat(),
                    session_id=session_id,
                    status="error",
                    error=error_message
                )
                
                try:
                    await websocket.send_text(response.model_dump_json())
                except Exception as e:
                    logger.error(f"发送错误消息失败: {e}")
                    self.disconnect(session_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息"""
        for session_id in list(self.active_connections.keys()):
            await self.send_message(session_id, message)
    
    def get_agent(self, session_id: str, agent_type: str):
        """获取会话智能体"""
        if session_id in self.session_agents:
            return self.session_agents[session_id].get(agent_type)
        return None
    
    def get_connection_count(self) -> int:
        """获取连接数"""
        return len(self.active_connections)
    
    def get_active_sessions(self) -> List[str]:
        """获取活跃会话"""
        return list(self.active_connections.keys())

# 全局连接管理器
manager = ConnectionManager()

# 消息处理器
class MessageHandler:
    """消息处理器"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager
    
    async def handle_message(self, session_id: str, message: WebSocketMessage):
        """处理消息"""
        try:
            message_type = message.type
            data = message.data
            
            if message_type == "search":
                await self._handle_search(session_id, data)
            elif message_type == "chat":
                await self._handle_chat(session_id, data)
            elif message_type == "react":
                await self._handle_react(session_id, data)
            elif message_type == "ping":
                await self._handle_ping(session_id, data)
            elif message_type == "get_status":
                await self._handle_get_status(session_id, data)
            else:
                await self.manager.send_error(session_id, f"未知消息类型: {message_type}")
        
        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)
            await self.manager.send_error(session_id, f"处理消息失败: {str(e)}")
    
    async def _handle_search(self, session_id: str, data: Dict[str, Any]):
        """处理搜索请求"""
        query = data.get("query")
        if not query:
            await self.manager.send_error(session_id, "缺少查询参数")
            return
        
        # 获取搜索智能体
        search_agent = self.manager.get_agent(session_id, "search")
        if not search_agent:
            await self.manager.send_error(session_id, "搜索智能体不可用")
            return
        
        # 解析参数
        strategy = SearchStrategy(data.get("strategy", "single_engine"))
        max_results = data.get("max_results", 10)
        engines = data.get("engines")
        
        if engines:
            engines = [SearchEngine(engine) for engine in engines if engine in [e.value for e in SearchEngine]]
        
        # 设置LLM提供商
        llm_provider = data.get("llm_provider")
        if llm_provider:
            search_agent.llm_provider = LLMProvider(llm_provider)
        
        # 发送搜索开始消息
        await self.manager.send_message(session_id, {
            "type": "search_start",
            "data": {"query": query, "strategy": strategy.value}
        })
        
        try:
            # 执行流式搜索
            async for chunk in search_agent.stream_search(query, strategy):
                await self.manager.send_message(session_id, {
                    "type": "search_chunk",
                    "data": chunk
                })
            
            # 发送搜索完成消息
            await self.manager.send_message(session_id, {
                "type": "search_complete",
                "data": {"query": query}
            })
        
        except Exception as e:
            await self.manager.send_error(session_id, f"搜索失败: {str(e)}")
    
    async def _handle_chat(self, session_id: str, data: Dict[str, Any]):
        """处理对话请求"""
        message = data.get("message")
        if not message:
            await self.manager.send_error(session_id, "缺少消息参数")
            return
        
        # 获取MindSearch智能体
        mindsearch_agent = self.manager.get_agent(session_id, "mindsearch")
        if not mindsearch_agent:
            await self.manager.send_error(session_id, "MindSearch智能体不可用")
            return
        
        # 解析参数
        max_turns = data.get("max_turns", 10)
        llm_provider = data.get("llm_provider")
        
        if llm_provider:
            mindsearch_agent.llm_provider = LLMProvider(llm_provider)
        
        # 发送对话开始消息
        await self.manager.send_message(session_id, {
            "type": "chat_start",
            "data": {"message": message}
        })
        
        try:
            # 执行流式对话
            async for chunk in mindsearch_agent.stream_chat(
                message=message,
                session_id=session_id,
                max_turns=max_turns
            ):
                await self.manager.send_message(session_id, {
                    "type": "chat_chunk",
                    "data": chunk
                })
            
            # 发送对话完成消息
            await self.manager.send_message(session_id, {
                "type": "chat_complete",
                "data": {"message": message}
            })
        
        except Exception as e:
            await self.manager.send_error(session_id, f"对话失败: {str(e)}")
    
    async def _handle_react(self, session_id: str, data: Dict[str, Any]):
        """处理ReAct请求"""
        problem = data.get("problem")
        if not problem:
            await self.manager.send_error(session_id, "缺少问题参数")
            return
        
        # 获取ReAct智能体
        react_agent = self.manager.get_agent(session_id, "react")
        if not react_agent:
            await self.manager.send_error(session_id, "ReAct智能体不可用")
            return
        
        # 解析参数
        max_steps = data.get("max_steps", 10)
        llm_provider = data.get("llm_provider")
        
        if llm_provider:
            react_agent.llm_provider = LLMProvider(llm_provider)
        
        # 发送ReAct开始消息
        await self.manager.send_message(session_id, {
            "type": "react_start",
            "data": {"problem": problem}
        })
        
        try:
            # 执行流式ReAct
            async for chunk in react_agent.stream_solve(
                problem=problem,
                max_steps=max_steps
            ):
                await self.manager.send_message(session_id, {
                    "type": "react_chunk",
                    "data": chunk
                })
            
            # 发送ReAct完成消息
            await self.manager.send_message(session_id, {
                "type": "react_complete",
                "data": {"problem": problem}
            })
        
        except Exception as e:
            await self.manager.send_error(session_id, f"ReAct失败: {str(e)}")
    
    async def _handle_ping(self, session_id: str, data: Dict[str, Any]):
        """处理ping请求"""
        await self.manager.send_message(session_id, {
            "type": "pong",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "message": "pong"
            }
        })
    
    async def _handle_get_status(self, session_id: str, data: Dict[str, Any]):
        """处理状态请求"""
        await self.manager.send_message(session_id, {
            "type": "status",
            "data": {
                "session_id": session_id,
                "connection_count": self.manager.get_connection_count(),
                "active_sessions": self.manager.get_active_sessions(),
                "timestamp": datetime.now().isoformat(),
                "agents": {
                    "mindsearch": "active",
                    "react": "active",
                    "search": "active"
                }
            }
        })

# 全局消息处理器
handler = MessageHandler(manager)

# WebSocket端点
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket端点"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            try:
                # 解析消息
                message_data = json.loads(data)
                message = WebSocketMessage(**message_data)
                
                # 处理消息
                await handler.handle_message(session_id, message)
            
            except ValidationError as e:
                await manager.send_error(session_id, f"消息格式错误: {str(e)}")
            except json.JSONDecodeError as e:
                await manager.send_error(session_id, f"JSON解析错误: {str(e)}")
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}", exc_info=True)
        manager.disconnect(session_id)

# 设置WebSocket路由
def setup_websocket(app: FastAPI):
    """设置WebSocket路由"""
    
    @app.websocket("/ws/{session_id}")
    async def websocket_route(websocket: WebSocket, session_id: str):
        await websocket_endpoint(websocket, session_id)
    
    # 添加WebSocket状态端点
    @app.get("/api/v1/websocket/status")
    async def websocket_status():
        """获取WebSocket状态"""
        return {
            "active_connections": manager.get_connection_count(),
            "active_sessions": manager.get_active_sessions(),
            "timestamp": datetime.now().isoformat()
        }
    
    logger.info("WebSocket路由已设置完成")