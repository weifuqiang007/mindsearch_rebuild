"""MindSearch 智能体

基于LangChain重构的MindSearch智能体，支持多轮对话和复杂查询处理
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from dataclasses import dataclass
from datetime import datetime

from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.agents import AgentExecutor
from langchain.tools import BaseTool
from langchain.callbacks.base import BaseCallbackHandler

from ..core.llm_manager import get_llm_manager, LLMProvider
from ..core.search_tools import get_search_manager, SearchResult
from ..core.query_decomposer import get_query_decomposer, QueryPlan, SubQuery
from ..core.reference_manager import get_reference_manager, Reference
from ..config import get_settings


@dataclass
class SearchStep:
    """搜索步骤"""
    step_id: str
    query: str
    search_results: List[SearchResult]
    analysis: str
    references: List[Reference]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "query": self.query,
            "search_results": [sr.to_dict() for sr in self.search_results],
            "analysis": self.analysis,
            "references": [ref.to_dict() for ref in self.references],
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SearchSession:
    """搜索会话"""
    session_id: str
    original_query: str
    query_plan: Optional[QueryPlan]
    search_steps: List[SearchStep]
    final_answer: str
    total_references: List[Reference]
    start_time: datetime
    end_time: Optional[datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "original_query": self.original_query,
            "query_plan": self.query_plan.to_dict() if self.query_plan else None,
            "search_steps": [step.to_dict() for step in self.search_steps],
            "final_answer": self.final_answer,
            "total_references": [ref.to_dict() for ref in self.total_references],
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


class StreamingCallbackHandler(BaseCallbackHandler):
    """流式响应回调处理器"""
    
    def __init__(self, callback_func=None):
        self.callback_func = callback_func
        self.current_step = ""
        self.current_content = ""
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """LLM开始时调用"""
        if self.callback_func:
            self.callback_func({
                "type": "llm_start",
                "data": {"prompts": prompts}
            })
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """新token时调用"""
        self.current_content += token
        if self.callback_func:
            self.callback_func({
                "type": "token",
                "data": {"token": token, "content": self.current_content}
            })
    
    def on_llm_end(self, response, **kwargs) -> None:
        """LLM结束时调用"""
        if self.callback_func:
            self.callback_func({
                "type": "llm_end",
                "data": {"response": self.current_content}
            })
        self.current_content = ""
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """工具开始时调用"""
        tool_name = serialized.get("name", "unknown")
        self.current_step = f"正在使用 {tool_name} 工具..."
        if self.callback_func:
            self.callback_func({
                "type": "tool_start",
                "data": {"tool_name": tool_name, "input": input_str}
            })
    
    def on_tool_end(self, output: str, **kwargs) -> None:
        """工具结束时调用"""
        if self.callback_func:
            self.callback_func({
                "type": "tool_end",
                "data": {"output": output}
            })


class MindSearchAgent:
    """MindSearch 智能体
    
    基于LangChain的MindSearch智能体实现
    """
    
    def __init__(self, 
                 llm_provider: Optional[LLMProvider] = None,
                 max_search_steps: int = 5,
                 max_results_per_search: int = 10):
        self.settings = get_settings()
        self.llm_manager = get_llm_manager()
        self.search_manager = get_search_manager()
        self.query_decomposer = get_query_decomposer(llm_provider)
        self.reference_manager = get_reference_manager()
        
        self.llm_provider = llm_provider
        self.max_search_steps = max_search_steps
        self.max_results_per_search = max_results_per_search
        
        # 系统提示
        self.system_prompt = """
你是一个专业的搜索助手，名为MindSearch。你的任务是帮助用户找到准确、全面的信息来回答他们的问题。

工作流程：
1. 分析用户的查询，理解其意图和需求
2. 将复杂查询分解为多个子问题
3. 逐步搜索和分析信息
4. 综合所有信息，提供准确、详细的答案
5. 提供可靠的信息来源和引用

注意事项：
- 始终基于搜索到的真实信息回答
- 如果信息不足或不确定，明确说明
- 提供多个角度的信息，保持客观
- 引用可靠的信息源
- 使用清晰、结构化的回答格式
"""
    
    def search(self, query: str, callback_func=None) -> SearchSession:
        """同步搜索"""
        return asyncio.run(self.asearch(query, callback_func))
    
    async def asearch(self, query: str, callback_func=None) -> SearchSession:
        """异步搜索"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        # 创建搜索会话
        session = SearchSession(
            session_id=session_id,
            original_query=query,
            query_plan=None,
            search_steps=[],
            final_answer="",
            total_references=[],
            start_time=start_time,
            end_time=None
        )
        
        try:
            # 1. 查询分解
            if callback_func:
                callback_func({"type": "status", "data": {"message": "正在分析查询..."}})
            
            query_plan = await self.query_decomposer.decompose_query(query)
            session.query_plan = query_plan
            
            # 2. 执行搜索步骤
            if callback_func:
                callback_func({"type": "status", "data": {"message": "开始搜索信息..."}})
            
            await self._execute_search_plan(session, callback_func)
            
            # 3. 生成最终答案
            if callback_func:
                callback_func({"type": "status", "data": {"message": "正在生成答案..."}})
            
            final_answer = await self._generate_final_answer(session, callback_func)
            session.final_answer = final_answer
            
            # 4. 收集所有引用
            session.total_references = self.reference_manager.get_references(min_credibility=0.3)
            
            session.end_time = datetime.now()
            
            if callback_func:
                callback_func({"type": "complete", "data": session.to_dict()})
            
            return session
            
        except Exception as e:
            session.final_answer = f"搜索过程中出现错误: {str(e)}"
            session.end_time = datetime.now()
            
            if callback_func:
                callback_func({"type": "error", "data": {"error": str(e)}})
            
            return session
    
    async def _execute_search_plan(self, session: SearchSession, callback_func=None):
        """执行搜索计划"""
        query_plan = session.query_plan
        if not query_plan:
            return
        
        # 按执行顺序处理子查询
        for stage_queries in query_plan.execution_order:
            # 并行执行同一阶段的查询
            tasks = []
            for sub_query_id in stage_queries:
                sub_query = next((sq for sq in query_plan.sub_queries if sq.id == sub_query_id), None)
                if sub_query:
                    task = self._execute_sub_query(sub_query, session, callback_func)
                    tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks)
    
    async def _execute_sub_query(self, sub_query: SubQuery, session: SearchSession, callback_func=None):
        """执行子查询"""
        if callback_func:
            callback_func({
                "type": "sub_query_start",
                "data": {"query": sub_query.query, "id": sub_query.id}
            })
        
        try:
            # 执行搜索
            search_results = await self.search_manager.search(
                query=sub_query.query,
                num_results=self.max_results_per_search
            )
            
            # 添加到引用管理器
            references = self.reference_manager.add_search_results(search_results, sub_query.query)
            
            # 分析搜索结果
            analysis = await self._analyze_search_results(sub_query, search_results)
            
            # 创建搜索步骤
            search_step = SearchStep(
                step_id=sub_query.id,
                query=sub_query.query,
                search_results=search_results,
                analysis=analysis,
                references=references,
                timestamp=datetime.now()
            )
            
            session.search_steps.append(search_step)
            
            if callback_func:
                callback_func({
                    "type": "sub_query_complete",
                    "data": search_step.to_dict()
                })
        
        except Exception as e:
            if callback_func:
                callback_func({
                    "type": "sub_query_error",
                    "data": {"query_id": sub_query.id, "error": str(e)}
                })
    
    async def _analyze_search_results(self, sub_query: SubQuery, search_results: List[SearchResult]) -> str:
        """分析搜索结果"""
        if not search_results:
            return "未找到相关信息"
        
        # 构建分析提示
        results_text = "\n".join([
            f"标题: {result.title}\n摘要: {result.snippet}\n来源: {result.url}\n"
            for result in search_results[:5]  # 只分析前5个结果
        ])
        
        analysis_prompt = f"""
请分析以下搜索结果，针对查询 "{sub_query.query}" 提供简洁的总结：

搜索结果：
{results_text}

请提供：
1. 关键信息总结
2. 主要发现
3. 信息的可靠性评估

保持回答简洁明了，重点突出最重要的信息。
"""
        
        analysis = await self.llm_manager.agenerate(
            prompt=analysis_prompt,
            provider=self.llm_provider
        )
        
        return analysis
    
    async def _generate_final_answer(self, session: SearchSession, callback_func=None) -> str:
        """生成最终答案"""
        if not session.search_steps:
            return "抱歉，未能找到相关信息来回答您的问题。"
        
        # 构建上下文
        context_parts = []
        for step in session.search_steps:
            context_parts.append(f"查询: {step.query}")
            context_parts.append(f"分析: {step.analysis}")
            context_parts.append("---")
        
        context = "\n".join(context_parts)
        
        # 生成最终答案的提示
        final_prompt = f"""
基于以下搜索和分析结果，请为用户的原始问题提供全面、准确的答案。

原始问题: {session.original_query}

搜索和分析结果:
{context}

请提供：
1. 直接回答用户的问题
2. 详细的解释和分析
3. 相关的背景信息
4. 如果有争议或不确定性，请说明

要求：
- 基于搜索到的真实信息
- 结构清晰，逻辑性强
- 客观公正，避免偏见
- 如果信息不足，诚实说明
"""
        
        # 流式生成答案
        if callback_func:
            answer_parts = []
            async for chunk in self.llm_manager.astream(
                prompt=final_prompt,
                provider=self.llm_provider
            ):
                answer_parts.append(chunk)
                callback_func({
                    "type": "answer_chunk",
                    "data": {"chunk": chunk, "content": "".join(answer_parts)}
                })
            
            final_answer = "".join(answer_parts)
        else:
            final_answer = await self.llm_manager.agenerate(
                prompt=final_prompt,
                provider=self.llm_provider
            )
        
        # 添加引用
        bibliography = self.reference_manager.generate_bibliography(min_credibility=0.5)
        if bibliography and bibliography != "暂无参考文献":
            final_answer += f"\n\n{bibliography}"
        
        return final_answer
    
    def get_session_statistics(self, session: SearchSession) -> Dict[str, Any]:
        """获取会话统计信息"""
        if not session.end_time:
            duration = 0
        else:
            duration = (session.end_time - session.start_time).total_seconds()
        
        total_results = sum(len(step.search_results) for step in session.search_steps)
        total_references = len(session.total_references)
        
        return {
            "session_id": session.session_id,
            "duration_seconds": duration,
            "total_search_steps": len(session.search_steps),
            "total_search_results": total_results,
            "total_references": total_references,
            "query_complexity": len(session.query_plan.sub_queries) if session.query_plan else 1,
            "average_credibility": sum(ref.credibility_score for ref in session.total_references) / total_references if total_references > 0 else 0
        }


class AsyncMindSearchAgent(MindSearchAgent):
    """异步MindSearch智能体
    
    专门用于异步操作的MindSearch智能体
    """
    
    async def stream_search(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """流式搜索"""
        async def stream_callback(data):
            yield data
        
        session = await self.asearch(query, stream_callback)
        
        # 最后发送完整会话信息
        yield {
            "type": "session_complete",
            "data": session.to_dict()
        }
    
    async def batch_search(self, queries: List[str]) -> List[SearchSession]:
        """批量搜索"""
        tasks = [self.asearch(query) for query in queries]
        sessions = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤异常
        valid_sessions = []
        for session in sessions:
            if isinstance(session, SearchSession):
                valid_sessions.append(session)
            else:
                # 创建错误会话
                error_session = SearchSession(
                    session_id=f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    original_query="批量查询错误",
                    query_plan=None,
                    search_steps=[],
                    final_answer=f"查询失败: {str(session)}",
                    total_references=[],
                    start_time=datetime.now(),
                    end_time=datetime.now()
                )
                valid_sessions.append(error_session)
        
        return valid_sessions