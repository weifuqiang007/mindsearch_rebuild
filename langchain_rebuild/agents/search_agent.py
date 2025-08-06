"""搜索智能体

专门处理搜索相关任务的智能体
"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..core.llm_manager import get_llm_manager, LLMProvider
from ..core.search_tools import get_search_manager, SearchResult, SearchEngine
from ..core.reference_manager import get_reference_manager, Reference


class SearchStrategy(Enum):
    """搜索策略"""
    SINGLE_ENGINE = "single_engine"  # 单引擎搜索
    MULTI_ENGINE = "multi_engine"    # 多引擎搜索
    ITERATIVE = "iterative"          # 迭代搜索
    FOCUSED = "focused"              # 聚焦搜索


@dataclass
class SearchTask:
    """搜索任务"""
    task_id: str
    query: str
    strategy: SearchStrategy
    engines: List[SearchEngine]
    max_results: int
    filters: Dict[str, Any]
    priority: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "query": self.query,
            "strategy": self.strategy.value,
            "engines": [engine.value for engine in self.engines],
            "max_results": self.max_results,
            "filters": self.filters,
            "priority": self.priority
        }


@dataclass
class SearchSession:
    """搜索会话"""
    session_id: str
    tasks: List[SearchTask]
    results: Dict[str, List[SearchResult]]
    references: List[Reference]
    summary: str
    start_time: datetime
    end_time: Optional[datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "tasks": [task.to_dict() for task in self.tasks],
            "results": {
                task_id: [result.to_dict() for result in results]
                for task_id, results in self.results.items()
            },
            "references": [ref.to_dict() for ref in self.references],
            "summary": self.summary,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


class SearchAgent:
    """搜索智能体
    
    专门处理各种搜索任务的智能体
    """
    
    def __init__(self, 
                 llm_provider: Optional[LLMProvider] = None,
                 default_max_results: int = 10):
        self.llm_manager = get_llm_manager()
        self.search_manager = get_search_manager()
        self.reference_manager = get_reference_manager()
        
        self.llm_provider = llm_provider
        self.default_max_results = default_max_results
        
        # 搜索优化提示
        self.query_optimization_prompt = """
请优化以下搜索查询，使其更加精确和有效：

原始查询: {query}
搜索目标: {objective}

请提供：
1. 优化后的查询词
2. 相关的关键词
3. 可能的同义词或变体
4. 建议的搜索策略

返回JSON格式：
{{
    "optimized_query": "优化后的查询",
    "keywords": ["关键词1", "关键词2"],
    "synonyms": ["同义词1", "同义词2"],
    "strategy": "建议的搜索策略"
}}
"""
        
        # 结果评估提示
        self.result_evaluation_prompt = """
请评估以下搜索结果的质量和相关性：

查询: {query}
搜索结果:
{results}

请为每个结果提供：
1. 相关性评分 (0-1)
2. 可信度评分 (0-1)
3. 信息价值评分 (0-1)
4. 简短评价

返回JSON格式的评估结果。
"""
    
    async def search(self, 
                   query: str, 
                   strategy: SearchStrategy = SearchStrategy.SINGLE_ENGINE,
                   engines: Optional[List[SearchEngine]] = None,
                   max_results: Optional[int] = None,
                   callback_func=None) -> SearchSession:
        """执行搜索"""
        session_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        if max_results is None:
            max_results = self.default_max_results
        
        if engines is None:
            engines = self.search_manager.list_engines()
        
        # 创建搜索任务
        task = SearchTask(
            task_id="main_task",
            query=query,
            strategy=strategy,
            engines=engines,
            max_results=max_results,
            filters={},
            priority=1
        )
        
        # 创建搜索会话
        session = SearchSession(
            session_id=session_id,
            tasks=[task],
            results={},
            references=[],
            summary="",
            start_time=start_time,
            end_time=None
        )
        
        try:
            if callback_func:
                callback_func({
                    "type": "search_start",
                    "data": {"session_id": session_id, "query": query}
                })
            
            # 执行搜索策略
            if strategy == SearchStrategy.SINGLE_ENGINE:
                results = await self._single_engine_search(task, callback_func)
            elif strategy == SearchStrategy.MULTI_ENGINE:
                results = await self._multi_engine_search(task, callback_func)
            elif strategy == SearchStrategy.ITERATIVE:
                results = await self._iterative_search(task, callback_func)
            elif strategy == SearchStrategy.FOCUSED:
                results = await self._focused_search(task, callback_func)
            else:
                results = await self._single_engine_search(task, callback_func)
            
            session.results[task.task_id] = results
            
            # 生成引用
            references = self.reference_manager.add_search_results(results, query)
            session.references = references
            
            # 生成摘要
            session.summary = await self._generate_search_summary(query, results)
            
            session.end_time = datetime.now()
            
            if callback_func:
                callback_func({
                    "type": "search_complete",
                    "data": session.to_dict()
                })
            
            return session
            
        except Exception as e:
            session.summary = f"搜索过程中出现错误: {str(e)}"
            session.end_time = datetime.now()
            
            if callback_func:
                callback_func({
                    "type": "search_error",
                    "data": {"error": str(e)}
                })
            
            return session
    
    async def _single_engine_search(self, task: SearchTask, callback_func=None) -> List[SearchResult]:
        """单引擎搜索"""
        engine = task.engines[0] if task.engines else None
        
        if callback_func:
            callback_func({
                "type": "engine_start",
                "data": {"engine": engine.value if engine else "default"}
            })
        
        results = await self.search_manager.search(
            query=task.query,
            num_results=task.max_results,
            engine=engine
        )
        
        return results
    
    async def _multi_engine_search(self, task: SearchTask, callback_func=None) -> List[SearchResult]:
        """多引擎搜索"""
        if callback_func:
            callback_func({
                "type": "multi_engine_start",
                "data": {"engines": [e.value for e in task.engines]}
            })
        
        # 并行搜索多个引擎
        engine_results = await self.search_manager.multi_engine_search(
            query=task.query,
            num_results=task.max_results,
            engines=task.engines
        )
        
        # 聚合结果
        aggregated_results = await self.search_manager.aggregate_search(
            query=task.query,
            num_results=task.max_results,
            engines=task.engines
        )
        
        return aggregated_results
    
    async def _iterative_search(self, task: SearchTask, callback_func=None) -> List[SearchResult]:
        """迭代搜索"""
        all_results = []
        current_query = task.query
        
        for iteration in range(3):  # 最多3次迭代
            if callback_func:
                callback_func({
                    "type": "iteration_start",
                    "data": {"iteration": iteration + 1, "query": current_query}
                })
            
            # 执行搜索
            results = await self.search_manager.search(
                query=current_query,
                num_results=task.max_results // 3,  # 每次搜索较少结果
                engine=task.engines[0] if task.engines else None
            )
            
            all_results.extend(results)
            
            # 如果是最后一次迭代，跳出
            if iteration == 2:
                break
            
            # 基于当前结果优化下一次查询
            if results:
                current_query = await self._optimize_query_from_results(task.query, results)
            
            if callback_func:
                callback_func({
                    "type": "iteration_complete",
                    "data": {"iteration": iteration + 1, "results_count": len(results)}
                })
        
        # 去重并排序
        unique_results = self._deduplicate_results(all_results)
        return unique_results[:task.max_results]
    
    async def _focused_search(self, task: SearchTask, callback_func=None) -> List[SearchResult]:
        """聚焦搜索"""
        if callback_func:
            callback_func({
                "type": "focused_search_start",
                "data": {"query": task.query}
            })
        
        # 首先优化查询
        optimized_query = await self._optimize_query(task.query, "获取最相关和权威的信息")
        
        # 执行搜索
        results = await self.search_manager.search(
            query=optimized_query,
            num_results=task.max_results * 2,  # 获取更多结果用于筛选
            engine=task.engines[0] if task.engines else None
        )
        
        # 评估和筛选结果
        if results:
            evaluated_results = await self._evaluate_results(task.query, results)
            # 按评分排序并取前N个
            evaluated_results.sort(key=lambda x: x.score, reverse=True)
            return evaluated_results[:task.max_results]
        
        return results
    
    async def _optimize_query(self, query: str, objective: str) -> str:
        """优化查询"""
        prompt = self.query_optimization_prompt.format(
            query=query,
            objective=objective
        )
        
        try:
            response = await self.llm_manager.agenerate(
                prompt=prompt,
                provider=self.llm_provider
            )
            
            # 尝试解析JSON响应
            import json
            optimization_result = json.loads(response)
            return optimization_result.get("optimized_query", query)
            
        except (json.JSONDecodeError, Exception):
            # 如果解析失败，返回原查询
            return query
    
    async def _optimize_query_from_results(self, original_query: str, results: List[SearchResult]) -> str:
        """基于搜索结果优化查询"""
        if not results:
            return original_query
        
        # 提取关键词
        keywords = set()
        for result in results[:3]:  # 只看前3个结果
            title_words = result.title.lower().split()
            snippet_words = result.snippet.lower().split()
            keywords.update(title_words[:5])  # 取标题前5个词
            keywords.update(snippet_words[:10])  # 取摘要前10个词
        
        # 过滤常见词
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '了', '吗', '呢', '吧', 'the', 'is', 'in', 'and', 'or', 'but'}
        meaningful_keywords = [kw for kw in keywords if len(kw) > 2 and kw not in stop_words]
        
        # 构建新查询
        if meaningful_keywords:
            new_query = f"{original_query} {' '.join(meaningful_keywords[:3])}"
            return new_query
        
        return original_query
    
    async def _evaluate_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """评估搜索结果"""
        if not results:
            return results
        
        # 构建结果文本
        results_text = "\n".join([
            f"{i+1}. 标题: {result.title}\n   摘要: {result.snippet}\n   来源: {result.url}"
            for i, result in enumerate(results[:5])  # 只评估前5个
        ])
        
        prompt = self.result_evaluation_prompt.format(
            query=query,
            results=results_text
        )
        
        try:
            response = await self.llm_manager.agenerate(
                prompt=prompt,
                provider=self.llm_provider
            )
            
            # 简单的评分逻辑（实际应用中可以更复杂）
            for i, result in enumerate(results):
                # 基于位置和内容质量的简单评分
                position_score = 1.0 - (i * 0.1)
                content_score = min(1.0, len(result.snippet) / 200)  # 内容长度评分
                title_score = min(1.0, len(result.title) / 50)  # 标题长度评分
                
                result.score = (position_score + content_score + title_score) / 3
            
        except Exception:
            # 如果评估失败，使用默认评分
            for i, result in enumerate(results):
                result.score = 1.0 - (i * 0.1)
        
        return results
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """去重搜索结果"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results
    
    async def _generate_search_summary(self, query: str, results: List[SearchResult]) -> str:
        """生成搜索摘要"""
        if not results:
            return f"未找到关于 '{query}' 的相关信息"
        
        summary_prompt = f"""
基于以下搜索结果，为查询 "{query}" 生成一个简洁的摘要：

搜索结果:
{chr(10).join([f"{i+1}. {result.title}: {result.snippet}" for i, result in enumerate(results[:5])])}

请提供：
1. 主要发现的总结
2. 信息的可靠性评估
3. 进一步研究的建议

保持摘要简洁明了。
"""
        
        try:
            summary = await self.llm_manager.agenerate(
                prompt=summary_prompt,
                provider=self.llm_provider
            )
            return summary
        except Exception as e:
            return f"找到 {len(results)} 个相关结果，但生成摘要时出现错误: {str(e)}"
    
    async def batch_search(self, 
                          queries: List[str], 
                          strategy: SearchStrategy = SearchStrategy.SINGLE_ENGINE) -> List[SearchSession]:
        """批量搜索"""
        tasks = []
        for query in queries:
            task = self.search(query, strategy)
            tasks.append(task)
        
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
                    tasks=[],
                    results={},
                    references=[],
                    summary=f"搜索失败: {str(session)}",
                    start_time=datetime.now(),
                    end_time=datetime.now()
                )
                valid_sessions.append(error_session)
        
        return valid_sessions
    
    async def stream_search(self, query: str, strategy: SearchStrategy = SearchStrategy.SINGLE_ENGINE) -> AsyncGenerator[Dict[str, Any], None]:
        """流式搜索"""
        async def stream_callback(data):
            yield data
        
        session = await self.search(query, strategy, callback_func=stream_callback)
        
        # 最后发送完整会话信息
        yield {
            "type": "session_complete",
            "data": session.to_dict()
        }
    
    def get_search_statistics(self, session: SearchSession) -> Dict[str, Any]:
        """获取搜索统计信息"""
        total_results = sum(len(results) for results in session.results.values())
        total_references = len(session.references)
        
        if session.end_time:
            duration = (session.end_time - session.start_time).total_seconds()
        else:
            duration = 0
        
        # 引擎分布
        engine_distribution = {}
        for task in session.tasks:
            for engine in task.engines:
                engine_name = engine.value
                engine_distribution[engine_name] = engine_distribution.get(engine_name, 0) + 1
        
        return {
            "session_id": session.session_id,
            "duration_seconds": duration,
            "total_tasks": len(session.tasks),
            "total_results": total_results,
            "total_references": total_references,
            "engine_distribution": engine_distribution,
            "average_results_per_task": total_results / len(session.tasks) if session.tasks else 0
        }