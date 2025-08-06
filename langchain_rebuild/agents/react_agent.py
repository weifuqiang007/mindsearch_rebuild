"""ReAct 智能体

基于ReAct (Reasoning and Acting) 模式的智能体实现
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..core.llm_manager import get_llm_manager, LLMProvider
from ..core.search_tools import get_search_manager, SearchResult
from ..core.reference_manager import get_reference_manager


class ActionType(Enum):
    """行动类型"""
    SEARCH = "search"
    ANALYZE = "analyze"
    SYNTHESIZE = "synthesize"
    FINISH = "finish"


@dataclass
class Thought:
    """思考步骤"""
    content: str
    reasoning: str
    confidence: float
    timestamp: datetime


@dataclass
class Action:
    """行动步骤"""
    action_type: ActionType
    parameters: Dict[str, Any]
    reasoning: str
    timestamp: datetime


@dataclass
class Observation:
    """观察结果"""
    content: str
    source: str
    confidence: float
    timestamp: datetime


@dataclass
class ReActStep:
    """ReAct步骤（思考-行动-观察）"""
    step_id: int
    thought: Thought
    action: Action
    observation: Observation
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "thought": {
                "content": self.thought.content,
                "reasoning": self.thought.reasoning,
                "confidence": self.thought.confidence,
                "timestamp": self.thought.timestamp.isoformat()
            },
            "action": {
                "action_type": self.action.action_type.value,
                "parameters": self.action.parameters,
                "reasoning": self.action.reasoning,
                "timestamp": self.action.timestamp.isoformat()
            },
            "observation": {
                "content": self.observation.content,
                "source": self.observation.source,
                "confidence": self.observation.confidence,
                "timestamp": self.observation.timestamp.isoformat()
            }
        }


class ReactAgent:
    """ReAct 智能体
    
    实现基于ReAct模式的推理和行动循环
    """
    
    def __init__(self, 
                 llm_provider: Optional[LLMProvider] = None,
                 max_steps: int = 10,
                 max_search_results: int = 5):
        self.llm_manager = get_llm_manager()
        self.search_manager = get_search_manager()
        self.reference_manager = get_reference_manager()
        
        self.llm_provider = llm_provider
        self.max_steps = max_steps
        self.max_search_results = max_search_results
        
        # ReAct 提示模板
        self.react_prompt_template = """
你是一个基于ReAct (Reasoning and Acting) 模式工作的智能助手。

你需要通过以下循环来解决问题：
1. Thought: 分析当前情况，思考下一步应该做什么
2. Action: 执行具体的行动
3. Observation: 观察行动的结果

可用的行动类型：
- search: 搜索信息 (参数: query)
- analyze: 分析已有信息 (参数: content, focus)
- synthesize: 综合信息得出结论 (参数: sources)
- finish: 完成任务并给出最终答案 (参数: answer)

请严格按照以下格式回应：

Thought: [你的思考过程]
Action: [行动类型]
Action Input: [JSON格式的参数]

用户问题: {query}

当前步骤: {step_number}
已有信息:
{context}

请开始你的思考和行动：
"""
        
        # 分析提示模板
        self.analysis_prompt = """
请分析以下信息，重点关注: {focus}

信息内容:
{content}

请提供：
1. 关键发现
2. 重要细节
3. 可能的问题或不一致之处
4. 进一步需要了解的信息
"""
        
        # 综合提示模板
        self.synthesis_prompt = """
请综合以下多个信息源，形成完整的理解：

{sources}

请提供：
1. 信息的一致性分析
2. 主要结论
3. 支持证据
4. 不确定性或争议点
"""
    
    async def solve(self, query: str, callback_func=None) -> Dict[str, Any]:
        """解决问题"""
        steps = []
        context = ""
        
        for step_number in range(1, self.max_steps + 1):
            if callback_func:
                callback_func({
                    "type": "step_start",
                    "data": {"step": step_number, "query": query}
                })
            
            try:
                # 执行ReAct步骤
                react_step = await self._execute_react_step(query, step_number, context)
                steps.append(react_step)
                
                # 更新上下文
                context += f"\n步骤 {step_number}:\n"
                context += f"思考: {react_step.thought.content}\n"
                context += f"行动: {react_step.action.action_type.value}\n"
                context += f"观察: {react_step.observation.content}\n"
                
                if callback_func:
                    callback_func({
                        "type": "step_complete",
                        "data": react_step.to_dict()
                    })
                
                # 检查是否完成
                if react_step.action.action_type == ActionType.FINISH:
                    break
                    
            except Exception as e:
                error_step = self._create_error_step(step_number, str(e))
                steps.append(error_step)
                
                if callback_func:
                    callback_func({
                        "type": "step_error",
                        "data": {"step": step_number, "error": str(e)}
                    })
                break
        
        # 构建结果
        result = {
            "query": query,
            "steps": [step.to_dict() for step in steps],
            "total_steps": len(steps),
            "completed": len(steps) > 0 and steps[-1].action.action_type == ActionType.FINISH,
            "final_answer": steps[-1].observation.content if steps else "未能完成任务",
            "references": [ref.to_dict() for ref in self.reference_manager.get_references()]
        }
        
        if callback_func:
            callback_func({
                "type": "complete",
                "data": result
            })
        
        return result
    
    async def _execute_react_step(self, query: str, step_number: int, context: str) -> ReActStep:
        """执行单个ReAct步骤"""
        # 1. 生成思考和行动
        prompt = self.react_prompt_template.format(
            query=query,
            step_number=step_number,
            context=context
        )
        
        response = await self.llm_manager.agenerate(
            prompt=prompt,
            provider=self.llm_provider
        )
        
        # 2. 解析响应
        thought, action = self._parse_react_response(response)
        
        # 3. 执行行动并获取观察
        observation = await self._execute_action(action)
        
        # 4. 创建ReAct步骤
        return ReActStep(
            step_id=step_number,
            thought=thought,
            action=action,
            observation=observation
        )
    
    def _parse_react_response(self, response: str) -> Tuple[Thought, Action]:
        """解析ReAct响应"""
        # 提取思考部分
        thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|$)', response, re.DOTALL)
        thought_content = thought_match.group(1).strip() if thought_match else "无法解析思考内容"
        
        # 提取行动类型
        action_match = re.search(r'Action:\s*(.+?)(?=Action Input:|$)', response, re.DOTALL)
        action_type_str = action_match.group(1).strip() if action_match else "search"
        
        try:
            action_type = ActionType(action_type_str.lower())
        except ValueError:
            action_type = ActionType.SEARCH
        
        # 提取行动参数
        input_match = re.search(r'Action Input:\s*(.+?)(?=\n\n|$)', response, re.DOTALL)
        input_str = input_match.group(1).strip() if input_match else "{}"
        
        try:
            action_parameters = json.loads(input_str)
        except json.JSONDecodeError:
            # 如果不是JSON格式，尝试简单解析
            if action_type == ActionType.SEARCH:
                action_parameters = {"query": input_str}
            else:
                action_parameters = {"content": input_str}
        
        # 创建思考和行动对象
        thought = Thought(
            content=thought_content,
            reasoning="基于当前情况的分析",
            confidence=0.8,
            timestamp=datetime.now()
        )
        
        action = Action(
            action_type=action_type,
            parameters=action_parameters,
            reasoning=thought_content,
            timestamp=datetime.now()
        )
        
        return thought, action
    
    async def _execute_action(self, action: Action) -> Observation:
        """执行行动"""
        try:
            if action.action_type == ActionType.SEARCH:
                return await self._execute_search_action(action)
            elif action.action_type == ActionType.ANALYZE:
                return await self._execute_analyze_action(action)
            elif action.action_type == ActionType.SYNTHESIZE:
                return await self._execute_synthesize_action(action)
            elif action.action_type == ActionType.FINISH:
                return await self._execute_finish_action(action)
            else:
                return Observation(
                    content=f"未知的行动类型: {action.action_type}",
                    source="system",
                    confidence=0.0,
                    timestamp=datetime.now()
                )
        except Exception as e:
            return Observation(
                content=f"执行行动时出错: {str(e)}",
                source="system",
                confidence=0.0,
                timestamp=datetime.now()
            )
    
    async def _execute_search_action(self, action: Action) -> Observation:
        """执行搜索行动"""
        query = action.parameters.get("query", "")
        if not query:
            return Observation(
                content="搜索查询为空",
                source="system",
                confidence=0.0,
                timestamp=datetime.now()
            )
        
        # 执行搜索
        search_results = await self.search_manager.search(
            query=query,
            num_results=self.max_search_results
        )
        
        if not search_results:
            return Observation(
                content=f"未找到关于 '{query}' 的相关信息",
                source="search",
                confidence=0.1,
                timestamp=datetime.now()
            )
        
        # 添加到引用管理器
        references = self.reference_manager.add_search_results(search_results, query)
        
        # 构建观察内容
        content_parts = [f"搜索查询: {query}", f"找到 {len(search_results)} 个结果:\n"]
        
        for i, result in enumerate(search_results, 1):
            content_parts.append(f"{i}. {result.title}")
            content_parts.append(f"   摘要: {result.snippet}")
            content_parts.append(f"   来源: {result.url}\n")
        
        return Observation(
            content="\n".join(content_parts),
            source="search",
            confidence=0.8,
            timestamp=datetime.now()
        )
    
    async def _execute_analyze_action(self, action: Action) -> Observation:
        """执行分析行动"""
        content = action.parameters.get("content", "")
        focus = action.parameters.get("focus", "关键信息")
        
        if not content:
            return Observation(
                content="没有提供要分析的内容",
                source="system",
                confidence=0.0,
                timestamp=datetime.now()
            )
        
        # 使用LLM进行分析
        analysis_prompt = self.analysis_prompt.format(
            content=content,
            focus=focus
        )
        
        analysis_result = await self.llm_manager.agenerate(
            prompt=analysis_prompt,
            provider=self.llm_provider
        )
        
        return Observation(
            content=analysis_result,
            source="analysis",
            confidence=0.7,
            timestamp=datetime.now()
        )
    
    async def _execute_synthesize_action(self, action: Action) -> Observation:
        """执行综合行动"""
        sources = action.parameters.get("sources", [])
        
        if not sources:
            return Observation(
                content="没有提供要综合的信息源",
                source="system",
                confidence=0.0,
                timestamp=datetime.now()
            )
        
        # 构建综合提示
        sources_text = "\n\n".join([
            f"信息源 {i+1}:\n{source}"
            for i, source in enumerate(sources)
        ])
        
        synthesis_prompt = self.synthesis_prompt.format(sources=sources_text)
        
        synthesis_result = await self.llm_manager.agenerate(
            prompt=synthesis_prompt,
            provider=self.llm_provider
        )
        
        return Observation(
            content=synthesis_result,
            source="synthesis",
            confidence=0.8,
            timestamp=datetime.now()
        )
    
    async def _execute_finish_action(self, action: Action) -> Observation:
        """执行完成行动"""
        answer = action.parameters.get("answer", "任务完成")
        
        # 添加引用信息
        references = self.reference_manager.get_references(min_credibility=0.5)
        if references:
            bibliography = self.reference_manager.generate_bibliography()
            answer += f"\n\n{bibliography}"
        
        return Observation(
            content=answer,
            source="final",
            confidence=0.9,
            timestamp=datetime.now()
        )
    
    def _create_error_step(self, step_number: int, error_message: str) -> ReActStep:
        """创建错误步骤"""
        thought = Thought(
            content=f"发生错误: {error_message}",
            reasoning="系统错误",
            confidence=0.0,
            timestamp=datetime.now()
        )
        
        action = Action(
            action_type=ActionType.FINISH,
            parameters={"answer": f"抱歉，处理过程中发生错误: {error_message}"},
            reasoning="错误处理",
            timestamp=datetime.now()
        )
        
        observation = Observation(
            content=f"任务因错误而终止: {error_message}",
            source="system",
            confidence=0.0,
            timestamp=datetime.now()
        )
        
        return ReActStep(
            step_id=step_number,
            thought=thought,
            action=action,
            observation=observation
        )
    
    async def stream_solve(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """流式解决问题"""
        async def stream_callback(data):
            yield data
        
        result = await self.solve(query, stream_callback)
        
        # 最后发送完整结果
        yield {
            "type": "final_result",
            "data": result
        }
    
    def get_step_statistics(self, steps: List[ReActStep]) -> Dict[str, Any]:
        """获取步骤统计信息"""
        if not steps:
            return {}
        
        action_counts = {}
        total_confidence = 0
        
        for step in steps:
            action_type = step.action.action_type.value
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
            total_confidence += step.observation.confidence
        
        return {
            "total_steps": len(steps),
            "action_distribution": action_counts,
            "average_confidence": total_confidence / len(steps),
            "completion_rate": 1.0 if steps[-1].action.action_type == ActionType.FINISH else 0.0
        }