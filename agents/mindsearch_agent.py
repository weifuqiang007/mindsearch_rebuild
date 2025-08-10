"""MindSearch 智能体

基于LangChain重构的MindSearch智能体，支持多轮对话和复杂查询处理
"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from dataclasses import dataclass
from datetime import datetime

from langchain.callbacks.base import BaseCallbackHandler
try:
    from core.simple_graph import SimpleSearchGraph, NodeType, NodeStatus
except ImportError:
    # 如果导入失败，尝试相对导入
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.simple_graph import SimpleSearchGraph, NodeType, NodeStatus

try:
    from core.llm_manager import get_llm_manager, LLMProvider
    from core.search_tools import get_search_manager, SearchResult
    from core.query_decomposer import get_query_decomposer, QueryPlan, SubQuery
    from core.reference_manager import get_reference_manager, Reference
    from config import get_settings
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.llm_manager import get_llm_manager, LLMProvider
    from core.search_tools import get_search_manager, SearchResult
    from core.query_decomposer import get_query_decomposer, QueryPlan, SubQuery
    from core.reference_manager import get_reference_manager, Reference
    from config import get_settings


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
        # 查询分解器.将一个单一的查询变成多个子查询
        self.query_decomposer = get_query_decomposer(llm_provider)
        # 全局引用管理器。对结果的概述
        self.reference_manager = get_reference_manager()
        #
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

        self.search_graph: Optional[SimpleSearchGraph] = None
        
    def _create_search_graph(self, query_plan: QueryPlan) -> SimpleSearchGraph:
        """根据查询计划创建搜索图"""
        graph = SimpleSearchGraph()
        
        # 创建根节点
        root_id = graph.add_node(
            name="root",
            content=f"原始查询: {query_plan.original_query}",
            node_type=NodeType.ROOT
        )
        
        # 为每个子查询创建搜索节点
        node_mapping = {"root": root_id}
        
        for sub_query in query_plan.sub_queries:
            search_node_id = graph.add_node(
                name=f"search_{sub_query.id}",
                content=sub_query.query,
                node_type=NodeType.SEARCH
            )
            node_mapping[sub_query.id] = search_node_id
            
            # 添加依赖关系
            if sub_query.dependencies:
                for dep_id in sub_query.dependencies:
                    if dep_id in node_mapping:
                        graph.add_edge(node_mapping[dep_id], search_node_id)
            else:
                # 如果没有依赖，连接到根节点
                graph.add_edge(root_id, search_node_id)
        
        # 创建结果汇总节点
        result_node_id = graph.add_node(
            name="result",
            content="汇总所有搜索结果",
            node_type=NodeType.RESULT
        )
        
        # 所有搜索节点都连接到结果节点
        for sub_query in query_plan.sub_queries:
            if sub_query.id in node_mapping:
                graph.add_edge(node_mapping[sub_query.id], result_node_id)
        
        # 创建结束节点
        end_node_id = graph.add_node(
            name="end",
            content="搜索完成",
            node_type=NodeType.END
        )
        graph.add_edge(result_node_id, end_node_id)
        
        # 标记根节点为已完成（作为起始点）
        graph.update_node_status(root_id, NodeStatus.COMPLETED)
        
        return graph
    
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
            
            # 2. 创建搜索图
            if callback_func:
                callback_func({"type": "status", "data": {"message": "创建搜索图..."}})
            
            self.search_graph = self._create_search_graph(query_plan)
            
            # 3. 基于图执行搜索步骤
            if callback_func:
                callback_func({"type": "status", "data": {"message": "开始搜索信息..."}})
                callback_func({"type": "graph_created", "data": self.search_graph.to_dict()})
            
            await self._execute_graph_search(session, callback_func)
            
            # 4. 生成最终答案
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
    
    async def _execute_graph_search(self, session: SearchSession, callback_func=None):
        """基于图执行搜索"""
        if not self.search_graph:
            return
        
        # 持续执行直到所有节点完成
        while True:
            # 获取可以执行的节点
            ready_nodes = self.search_graph.get_ready_nodes()
            
            if not ready_nodes:
                # 检查是否还有未完成的节点
                pending_nodes = [nid for nid, node in self.search_graph.nodes.items() 
                               if node.status == NodeStatus.PENDING]
                if not pending_nodes:
                    break  # 所有节点都已完成
                else:
                    # 检查是否有节点因为依赖失败而无法执行
                    blocked_nodes = []
                    for node_id in pending_nodes:
                        parent_nodes = self.search_graph.get_parent_nodes(node_id)
                        if parent_nodes and any(self.search_graph.nodes[pid].status == NodeStatus.FAILED for pid in parent_nodes):
                            # 标记为失败（因为依赖失败）
                            self.search_graph.update_node_status(node_id, NodeStatus.FAILED, error="依赖节点执行失败")
                            blocked_nodes.append(node_id)
                    
                    if blocked_nodes:
                        if callback_func:
                            callback_func({"type": "warning", "data": {"message": f"因依赖失败跳过 {len(blocked_nodes)} 个节点"}})
                        continue  # 继续下一轮检查
                    else:
                        # 真正的循环依赖
                        if callback_func:
                            callback_func({"type": "error", "data": {"error": "检测到循环依赖"}})
                        break
            
            # 并行执行所有准备好的搜索节点
            search_tasks = []
            for node_id in ready_nodes:
                node = self.search_graph.nodes[node_id]
                if node.node_type == NodeType.SEARCH:
                    # 标记为运行中
                    self.search_graph.update_node_status(node_id, NodeStatus.RUNNING)
                    
                    # 找到对应的子查询
                    sub_query = self._find_sub_query_by_node(node, session.query_plan)
                    if sub_query:
                        task = self._execute_graph_sub_query(sub_query, node_id, session, callback_func)
                        search_tasks.append(task)
                elif node.node_type == NodeType.RESULT:
                    # 处理结果汇总节点
                    self.search_graph.update_node_status(node_id, NodeStatus.RUNNING)
                    await self._process_result_node(node_id, session, callback_func)
                    self.search_graph.update_node_status(node_id, NodeStatus.COMPLETED)
                elif node.node_type == NodeType.END:
                    # 处理结束节点
                    self.search_graph.update_node_status(node_id, NodeStatus.COMPLETED)
                    if callback_func:
                        callback_func({"type": "graph_complete", "data": self.search_graph.to_dict()})
            
            # 等待所有搜索任务完成
            if search_tasks:
                await asyncio.gather(*search_tasks, return_exceptions=True)
    
    def _find_sub_query_by_node(self, node: 'GraphNode', query_plan: QueryPlan) -> Optional['SubQuery']:
        """根据节点找到对应的子查询"""
        # 从节点名称中提取子查询ID
        if node.name.startswith("search_"):
            sub_query_id = node.name[7:]  # 移除 "search_" 前缀
            return next((sq for sq in query_plan.sub_queries if sq.id == sub_query_id), None)
        return None
    
    async def _process_result_node(self, node_id: str, session: SearchSession, callback_func=None):
        """处理结果汇总节点"""
        if callback_func:
            callback_func({"type": "status", "data": {"message": "汇总搜索结果..."}})
        
        # 这里可以添加额外的结果处理逻辑
        # 目前只是标记完成
        pass
    
    async def _execute_graph_sub_query(self, sub_query: SubQuery, node_id: str, session: SearchSession, callback_func=None):
        """执行图中的子查询"""
        if callback_func:
            callback_func({
                "type": "sub_query_start",
                "data": {"query": sub_query.query, "id": sub_query.id, "node_id": node_id}
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
            
            # 更新图节点状态
            self.search_graph.update_node_status(node_id, NodeStatus.COMPLETED, result=search_step.to_dict())
            
            if callback_func:
                callback_func({
                    "type": "sub_query_complete",
                    "data": search_step.to_dict()
                })
                callback_func({
                    "type": "node_updated",
                    "data": {"node_id": node_id, "status": "completed"}
                })
        
        except Exception as e:
            # 更新图节点状态为失败
            self.search_graph.update_node_status(node_id, NodeStatus.FAILED, error=str(e))
            
            if callback_func:
                callback_func({
                    "type": "sub_query_error",
                    "data": {"query_id": sub_query.id, "node_id": node_id, "error": str(e)}
                })
                callback_func({
                    "type": "node_updated",
                    "data": {"node_id": node_id, "status": "failed", "error": str(e)}
                })
    
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
        
        # 图统计信息
        graph_stats = self.get_graph_statistics() if self.search_graph else {}
        
        stats = {
            "session_id": session.session_id,
            "duration_seconds": duration,
            "total_search_steps": len(session.search_steps),
            "total_search_results": total_results,
            "total_references": total_references,
            "query_complexity": len(session.query_plan.sub_queries) if session.query_plan else 1,
            "average_credibility": sum(ref.credibility_score for ref in session.total_references) / total_references if total_references > 0 else 0
        }
        
        # 添加图统计信息
        if graph_stats:
            stats["graph_statistics"] = graph_stats
        
        return stats
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """获取图执行统计信息"""
        if not self.search_graph:
            return {}
        
        node_status_count = {}
        for status in NodeStatus:
            node_status_count[status.value] = 0
        
        for node in self.search_graph.nodes.values():
            node_status_count[node.status.value] += 1
        
        total_nodes = len(self.search_graph.nodes)
        total_edges = len(self.search_graph.edges)
        
        # 计算执行效率
        completed_nodes = node_status_count.get(NodeStatus.COMPLETED.value, 0)
        failed_nodes = node_status_count.get(NodeStatus.FAILED.value, 0)
        success_rate = completed_nodes / total_nodes if total_nodes > 0 else 0
        
        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "node_status_distribution": node_status_count,
            "success_rate": success_rate,
            "failed_nodes": failed_nodes,
            "graph_structure": self.search_graph.to_dict()
        }
    
    def visualize_search_graph(self, save_path: Optional[str] = None, 
                              show_labels: bool = True, 
                              figsize: tuple = (12, 8),
                              title: str = "MindSearch 搜索图") -> None:
        """可视化当前搜索图
        
        Args:
            save_path: 保存图片的路径，如果为None则显示图片
            show_labels: 是否显示节点标签
            figsize: 图片大小
            title: 图片标题
        """
        if not hasattr(self, 'search_graph') or not self.search_graph:
            print("❌ 当前没有可用的搜索图，请先执行搜索")
            return
        
        self.search_graph.visualize_graph(
            save_path=save_path,
            show_labels=show_labels,
            figsize=figsize,
            title=title
        )
    
    def print_search_graph(self) -> None:
        """打印当前搜索图的文本结构"""
        if not hasattr(self, 'search_graph') or not self.search_graph:
            print("❌ 当前没有可用的搜索图，请先执行搜索")
            return
        
        self.search_graph.print_graph_structure()
    
    def export_graph_dot(self, filename: str = "search_graph.dot") -> None:
        """导出搜索图为DOT格式
        
        Args:
            filename: 输出文件名
        """
        if not hasattr(self, 'search_graph') or not self.search_graph:
            print("❌ 当前没有可用的搜索图，请先执行搜索")
            return
        
        self.search_graph.export_dot(filename)


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


# 导出常用类和枚举
__all__ = ['MindSearchAgent', 'AsyncMindSearchAgent', 'LLMProvider', 'SearchSession']