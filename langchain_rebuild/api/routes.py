"""API路由

定义所有的RESTful端点
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import asyncio
import json
from datetime import datetime

from ..agents.mindsearch_agent import MindSearchAgent, AsyncMindSearchAgent
from ..agents.react_agent import ReactAgent
from ..agents.search_agent import SearchAgent, SearchStrategy
from ..core.llm_manager import LLMProvider
from ..core.search_tools import SearchEngine
from ..config import get_llm_config, get_search_config, get_agent_config

# 请求模型
class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., description="搜索查询")
    max_results: Optional[int] = Field(10, description="最大结果数")
    engines: Optional[List[str]] = Field(None, description="搜索引擎列表")
    strategy: Optional[str] = Field("single_engine", description="搜索策略")
    llm_provider: Optional[str] = Field(None, description="LLM提供商")

class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID")
    max_turns: Optional[int] = Field(10, description="最大对话轮数")
    llm_provider: Optional[str] = Field(None, description="LLM提供商")
    stream: Optional[bool] = Field(False, description="是否流式响应")

class ReactRequest(BaseModel):
    """ReAct请求"""
    problem: str = Field(..., description="要解决的问题")
    max_steps: Optional[int] = Field(10, description="最大步骤数")
    llm_provider: Optional[str] = Field(None, description="LLM提供商")
    stream: Optional[bool] = Field(False, description="是否流式响应")

# 响应模型
class SearchResponse(BaseModel):
    """搜索响应"""
    session_id: str
    query: str
    results: List[Dict[str, Any]]
    references: List[Dict[str, Any]]
    summary: str
    duration: float
    metadata: Dict[str, Any]

class ChatResponse(BaseModel):
    """对话响应"""
    session_id: str
    message: str
    response: str
    references: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class ReactResponse(BaseModel):
    """ReAct响应"""
    problem: str
    solution: str
    steps: List[Dict[str, Any]]
    metadata: Dict[str, Any]

# 依赖注入
def get_mindsearch_agent() -> MindSearchAgent:
    """获取MindSearch智能体"""
    return MindSearchAgent()

def get_async_mindsearch_agent() -> AsyncMindSearchAgent:
    """获取异步MindSearch智能体"""
    return AsyncMindSearchAgent()

def get_react_agent() -> ReactAgent:
    """获取ReAct智能体"""
    return ReactAgent()

def get_search_agent() -> SearchAgent:
    """获取搜索智能体"""
    return SearchAgent()

# 路由器
api_router = APIRouter(prefix="/api/v1")
search_router = APIRouter(prefix="/search", tags=["搜索"])
chat_router = APIRouter(prefix="/chat", tags=["对话"])
react_router = APIRouter(prefix="/react", tags=["ReAct"])

# 搜索相关端点
@search_router.post("/", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    agent: SearchAgent = Depends(get_search_agent)
) -> SearchResponse:
    """执行搜索"""
    try:
        # 解析搜索引擎
        engines = None
        if request.engines:
            engines = [SearchEngine(engine) for engine in request.engines if engine in [e.value for e in SearchEngine]]
        
        # 解析搜索策略
        strategy = SearchStrategy(request.strategy) if request.strategy else SearchStrategy.SINGLE_ENGINE
        
        # 设置LLM提供商
        if request.llm_provider:
            agent.llm_provider = LLMProvider(request.llm_provider)
        
        start_time = datetime.now()
        
        # 执行搜索
        session = await agent.search(
            query=request.query,
            strategy=strategy,
            engines=engines,
            max_results=request.max_results
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 构建响应
        return SearchResponse(
            session_id=session.session_id,
            query=request.query,
            results=[result.to_dict() for results in session.results.values() for result in results],
            references=[ref.to_dict() for ref in session.references],
            summary=session.summary,
            duration=duration,
            metadata=agent.get_search_statistics(session)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@search_router.post("/stream")
async def search_stream(
    request: SearchRequest,
    agent: SearchAgent = Depends(get_search_agent)
):
    """流式搜索"""
    try:
        # 解析参数
        engines = None
        if request.engines:
            engines = [SearchEngine(engine) for engine in request.engines if engine in [e.value for e in SearchEngine]]
        
        strategy = SearchStrategy(request.strategy) if request.strategy else SearchStrategy.SINGLE_ENGINE
        
        if request.llm_provider:
            agent.llm_provider = LLMProvider(request.llm_provider)
        
        async def generate():
            async for chunk in agent.stream_search(request.query, strategy):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流式搜索失败: {str(e)}")

@search_router.post("/batch")
async def batch_search(
    requests: List[SearchRequest],
    agent: SearchAgent = Depends(get_search_agent)
) -> List[SearchResponse]:
    """批量搜索"""
    try:
        queries = [req.query for req in requests]
        strategy = SearchStrategy(requests[0].strategy) if requests and requests[0].strategy else SearchStrategy.SINGLE_ENGINE
        
        sessions = await agent.batch_search(queries, strategy)
        
        responses = []
        for i, session in enumerate(sessions):
            response = SearchResponse(
                session_id=session.session_id,
                query=requests[i].query if i < len(requests) else "",
                results=[result.to_dict() for results in session.results.values() for result in results],
                references=[ref.to_dict() for ref in session.references],
                summary=session.summary,
                duration=0,  # 批量搜索不计算单个持续时间
                metadata=agent.get_search_statistics(session)
            )
            responses.append(response)
        
        return responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量搜索失败: {str(e)}")

# 对话相关端点
@chat_router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent: AsyncMindSearchAgent = Depends(get_async_mindsearch_agent)
) -> ChatResponse:
    """对话"""
    try:
        # 设置LLM提供商
        if request.llm_provider:
            agent.llm_provider = LLMProvider(request.llm_provider)
        
        # 执行对话
        response = await agent.chat(
            message=request.message,
            session_id=request.session_id,
            max_turns=request.max_turns
        )
        
        return ChatResponse(
            session_id=response.get("session_id", ""),
            message=request.message,
            response=response.get("response", ""),
            references=response.get("references", []),
            metadata=response.get("metadata", {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")

@chat_router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    agent: AsyncMindSearchAgent = Depends(get_async_mindsearch_agent)
):
    """流式对话"""
    try:
        if request.llm_provider:
            agent.llm_provider = LLMProvider(request.llm_provider)
        
        async def generate():
            async for chunk in agent.stream_chat(
                message=request.message,
                session_id=request.session_id,
                max_turns=request.max_turns
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流式对话失败: {str(e)}")

# ReAct相关端点
@react_router.post("/", response_model=ReactResponse)
async def react_solve(
    request: ReactRequest,
    agent: ReactAgent = Depends(get_react_agent)
) -> ReactResponse:
    """ReAct问题解决"""
    try:
        if request.llm_provider:
            agent.llm_provider = LLMProvider(request.llm_provider)
        
        result = await agent.solve_async(
            problem=request.problem,
            max_steps=request.max_steps
        )
        
        return ReactResponse(
            problem=request.problem,
            solution=result.get("solution", ""),
            steps=[step.to_dict() for step in result.get("steps", [])],
            metadata=result.get("metadata", {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ReAct解决失败: {str(e)}")

@react_router.post("/stream")
async def react_solve_stream(
    request: ReactRequest,
    agent: ReactAgent = Depends(get_react_agent)
):
    """流式ReAct问题解决"""
    try:
        if request.llm_provider:
            agent.llm_provider = LLMProvider(request.llm_provider)
        
        async def generate():
            async for chunk in agent.stream_solve(
                problem=request.problem,
                max_steps=request.max_steps
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流式ReAct解决失败: {str(e)}")

# 系统相关端点
@api_router.get("/config")
async def get_config() -> Dict[str, Any]:
    """获取系统配置"""
    llm_config = get_llm_config()
    search_config = get_search_config()
    agent_config = get_agent_config()
    
    return {
        "llm": {
            "providers": [provider.value for provider in LLMProvider],
            "default_provider": llm_config.default_provider,
            "max_tokens": llm_config.max_tokens,
            "temperature": llm_config.temperature
        },
        "search": {
            "engines": [engine.value for engine in SearchEngine],
            "default_engine": search_config.default_engine,
            "max_results": search_config.max_results,
            "timeout": search_config.timeout
        },
        "agent": {
            "max_iterations": agent_config.max_iterations,
            "max_execution_time": agent_config.max_execution_time
        }
    }

@api_router.get("/status")
async def get_status() -> Dict[str, Any]:
    """获取系统状态"""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "llm_manager": "active",
            "search_manager": "active",
            "reference_manager": "active",
            "agents": "active"
        }
    }

# 注册所有路由
def register_routes(app):
    """注册所有路由"""
    # 注册子路由
    api_router.include_router(search_router)
    api_router.include_router(chat_router)
    api_router.include_router(react_router)
    
    # 注册主路由
    app.include_router(api_router)