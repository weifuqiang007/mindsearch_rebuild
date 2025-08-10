"""查询分解器

将复杂的用户查询分解为多个子问题，支持层次化的问题分解
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .llm_manager import get_llm_manager, LLMProvider


class QueryType(Enum):
    """查询类型枚举"""
    FACTUAL = "factual"  # 事实性查询
    COMPARATIVE = "comparative"  # 比较性查询
    ANALYTICAL = "analytical"  # 分析性查询
    TEMPORAL = "temporal"  # 时间性查询
    CAUSAL = "causal"  # 因果性查询
    PROCEDURAL = "procedural"  # 程序性查询
    OPINION = "opinion"  # 观点性查询


@dataclass
class SubQuery:
    """子查询数据类"""
    id: str
    query: str
    query_type: QueryType
    priority: int  # 优先级 1-10
    dependencies: List[str]  # 依赖的其他子查询ID
    keywords: List[str]  # 关键词
    expected_sources: List[str]  # 期望的信息源类型
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['query_type'] = self.query_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubQuery':
        """从字典创建"""
        data['query_type'] = QueryType(data['query_type'])
        return cls(**data)


@dataclass
class QueryPlan:
    """查询计划"""
    original_query: str
    sub_queries: List[SubQuery]
    execution_order: List[List[str]]  # 执行顺序（支持并行）
    estimated_time: int  # 预估执行时间（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'original_query': self.original_query,
            'sub_queries': [sq.to_dict() for sq in self.sub_queries],
            'execution_order': self.execution_order,
            'estimated_time': self.estimated_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryPlan':
        """从字典创建"""
        sub_queries = [SubQuery.from_dict(sq) for sq in data['sub_queries']]
        return cls(
            original_query=data['original_query'],
            sub_queries=sub_queries,
            execution_order=data['execution_order'],
            estimated_time=data['estimated_time']
        )


class QueryDecomposer:
    """查询分解器
    
    使用LLM将复杂查询分解为多个子问题
    """
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_manager = get_llm_manager()
        self.llm_provider = llm_provider
        
        # 分解提示模板
        self.decomposition_prompt = """
你是一个专业的查询分析师。请将用户的复杂查询分解为多个具体的子问题。

用户查询：{query}

请按照以下JSON格式返回分解结果：

{{
    "analysis": "对查询的分析说明",
    "sub_queries": [
        {{
            "id": "q1",
            "query": "具体的子问题",
            "query_type": "factual|comparative|analytical|temporal|causal|procedural|opinion",
            "priority": 1-10,
            "dependencies": ["依赖的其他子查询ID"],
            "keywords": ["关键词1", "关键词2"],
            "expected_sources": ["学术论文", "新闻报道", "官方网站", "统计数据"]
        }}
    ],
    "execution_strategy": "执行策略说明"
}}

分解原则：
1. 每个子问题应该是独立可搜索的
2. 子问题之间可以有依赖关系
3. 优先级高的问题应该先执行
4. 考虑信息的时效性和权威性
5. 避免重复和冗余的子问题

请确保返回有效的JSON格式。
"""
        
        # 查询类型识别提示
        self.type_identification_prompt = """
请分析以下查询的类型和特征：

查询：{query}

请返回JSON格式的分析结果：
{{
    "primary_type": "主要查询类型",
    "complexity": "simple|medium|complex",
    "requires_decomposition": true/false,
    "key_aspects": ["关键方面1", "关键方面2"],
    "suggested_approach": "建议的处理方法"
}}
"""
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """分析查询类型和复杂度"""
        prompt = self.type_identification_prompt.format(query=query)
        
        response = await self.llm_manager.agenerate(
            prompt=prompt,
            provider=self.llm_provider
        )

        try:
            return json.loads(self._extract_json(response))
        except (json.JSONDecodeError, ValueError) as e:
            # 如果解析失败，返回默认分析
            return {
                "primary_type": "factual",  # 事实的
                "complexity": "medium",
                "requires_decomposition": True,
                "key_aspects": [query],
                "suggested_approach": "standard_decomposition"  # 标准分解
            }
    
    async def decompose_query(self, query: str) -> QueryPlan:
        """分解查询为子问题"""
        # 首先分析查询
        analysis = await self.analyze_query(query)
        
        # 如果不需要分解，直接返回单个查询
        if not analysis.get("requires_decomposition", True):
            sub_query = SubQuery(
                id="q1",
                query=query,
                query_type=QueryType.FACTUAL,
                priority=10,
                dependencies=[],
                keywords=analysis.get("key_aspects", [query]),
                expected_sources=["搜索引擎"]
            )
            
            return QueryPlan(
                original_query=query,
                sub_queries=[sub_query],
                execution_order=[["q1"]],
                estimated_time=30
            )
        
        # 执行分解
        prompt = self.decomposition_prompt.format(query=query)

        # 这一块是不是重复了？
        response = await self.llm_manager.agenerate(
            prompt=prompt,
            provider=self.llm_provider
        )
        
        try:
            decomposition_result = json.loads(self._extract_json(response))
            return self._build_query_plan(query, decomposition_result)
        except (json.JSONDecodeError, ValueError) as e:
            # 如果分解失败，使用简单分解策略
            return self._simple_decomposition(query)
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON"""
        # 尝试找到JSON块
        json_pattern = r'```json\s*({.*?})\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        
        # 尝试找到大括号包围的内容
        brace_pattern = r'{.*}'
        match = re.search(brace_pattern, text, re.DOTALL)
        if match:
            return match.group(0)
        
        # 如果都找不到，返回原文本
        return text
    
    def _build_query_plan(self, original_query: str, decomposition_result: Dict[str, Any]) -> QueryPlan:
        """构建查询计划"""
        sub_queries = []
        
        for sq_data in decomposition_result.get("sub_queries", []):
            try:
                query_type = QueryType(sq_data.get("query_type", "factual"))
            except ValueError:
                query_type = QueryType.FACTUAL
            
            sub_query = SubQuery(
                id=sq_data.get("id", f"q{len(sub_queries) + 1}"),
                query=sq_data.get("query", ""),
                query_type=query_type,
                priority=sq_data.get("priority", 5),
                dependencies=sq_data.get("dependencies", []),
                keywords=sq_data.get("keywords", []),
                expected_sources=sq_data.get("expected_sources", [])
            )
            sub_queries.append(sub_query)
        
        # 计算执行顺序
        execution_order = self._calculate_execution_order(sub_queries)
        
        # 估算执行时间
        estimated_time = len(sub_queries) * 30  # 每个子查询预估30秒
        
        return QueryPlan(
            original_query=original_query,
            sub_queries=sub_queries,
            execution_order=execution_order,
            estimated_time=estimated_time
        )
    
    def _simple_decomposition(self, query: str) -> QueryPlan:
        """简单分解策略（备用方案）"""
        # 基于关键词的简单分解
        keywords = self._extract_keywords(query)
        
        sub_queries = []
        for i, keyword in enumerate(keywords[:3]):  # 最多3个子查询
            sub_query = SubQuery(
                id=f"q{i+1}",
                query=f"{keyword} 相关信息",
                query_type=QueryType.FACTUAL,
                priority=10 - i,
                dependencies=[],
                keywords=[keyword],
                expected_sources=["搜索引擎"]
            )
            sub_queries.append(sub_query)
        
        # 如果没有提取到关键词，使用原查询
        if not sub_queries:
            sub_query = SubQuery(
                id="q1",
                query=query,
                query_type=QueryType.FACTUAL,
                priority=10,
                dependencies=[],
                keywords=[query],
                expected_sources=["搜索引擎"]
            )
            sub_queries.append(sub_query)
        
        execution_order = [[sq.id for sq in sub_queries]]  # 并行执行
        
        return QueryPlan(
            original_query=query,
            sub_queries=sub_queries,
            execution_order=execution_order,
            estimated_time=len(sub_queries) * 30
        )
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（可以使用更复杂的NLP方法）
        import jieba
        
        # 分词
        words = jieba.lcut(query)
        
        # 过滤停用词和短词
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '了', '吗', '呢', '吧'}
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        return keywords[:5]  # 返回前5个关键词

    def identify_query_type(self, query: str) -> QueryType:
        """识别查询类型（同步版本）"""
        # 简单的规则基础识别
        query_lower = query.lower()
        
        # 比较性查询
        if any(word in query_lower for word in ['比较', '对比', '区别', '差异', '哪个更好', 'vs', '和']):
            return QueryType.COMPARATIVE
        
        # 时间性查询
        if any(word in query_lower for word in ['什么时候', '何时', '时间', '历史', '发展', '变化']):
            return QueryType.TEMPORAL
        
        # 因果性查询
        if any(word in query_lower for word in ['为什么', '原因', '导致', '影响', '结果', '后果']):
            return QueryType.CAUSAL
        
        # 程序性查询
        if any(word in query_lower for word in ['如何', '怎么', '步骤', '方法', '流程', '教程']):
            return QueryType.PROCEDURAL
        
        # 观点性查询
        if any(word in query_lower for word in ['观点', '看法', '评价', '意见', '认为', '觉得']):
            return QueryType.OPINION
        
        # 分析性查询
        if any(word in query_lower for word in ['分析', '解释', '说明', '阐述', '详细']):
            return QueryType.ANALYTICAL
        
        # 默认为事实性查询
        return QueryType.FACTUAL

    def extract_keywords(self, query: str) -> List[str]:
        """提取关键词（公开方法）"""
        return self._extract_keywords(query)

    def _calculate_execution_order(self, sub_queries: List[SubQuery]) -> List[List[str]]:
        """计算执行顺序（考虑依赖关系）"""
        # 构建依赖图
        dependency_graph = {sq.id: sq.dependencies for sq in sub_queries}
        query_map = {sq.id: sq for sq in sub_queries}
        
        execution_order = []
        executed = set()
        
        while len(executed) < len(sub_queries):
            # 找到可以执行的查询（没有未满足的依赖）
            ready_queries = []
            
            for sq in sub_queries:
                if sq.id not in executed:
                    dependencies_met = all(dep in executed for dep in sq.dependencies)
                    if dependencies_met:
                        ready_queries.append(sq.id)
            
            if not ready_queries:
                # 如果没有可执行的查询，可能存在循环依赖，强制执行剩余查询
                remaining = [sq.id for sq in sub_queries if sq.id not in executed]
                ready_queries = remaining
            
            # 按优先级排序
            ready_queries.sort(key=lambda qid: query_map[qid].priority, reverse=True)
            
            execution_order.append(ready_queries)
            executed.update(ready_queries)
        
        return execution_order
    
    async def refine_sub_query(self, sub_query: SubQuery, context: str = "") -> SubQuery:
        """根据上下文优化子查询"""
        if not context:
            return sub_query
        
        refine_prompt = f"""
基于以下上下文信息，请优化这个子查询：

原始子查询：{sub_query.query}
上下文信息：{context}

请返回优化后的查询，使其更加具体和准确：
"""
        
        response = await self.llm_manager.agenerate(
            prompt=refine_prompt,
            provider=self.llm_provider
        )
        
        # 创建优化后的子查询
        refined_sub_query = SubQuery(
            id=sub_query.id,
            query=response.strip(),
            query_type=sub_query.query_type,
            priority=sub_query.priority,
            dependencies=sub_query.dependencies,
            keywords=sub_query.keywords,
            expected_sources=sub_query.expected_sources
        )
        
        return refined_sub_query
    
    def get_execution_statistics(self, query_plan: QueryPlan) -> Dict[str, Any]:
        """获取执行统计信息"""
        total_queries = len(query_plan.sub_queries)
        parallel_stages = len(query_plan.execution_order)
        
        query_types = {}
        for sq in query_plan.sub_queries:
            query_type = sq.query_type.value
            query_types[query_type] = query_types.get(query_type, 0) + 1
        
        return {
            "total_sub_queries": total_queries,
            "parallel_stages": parallel_stages,
            "estimated_time": query_plan.estimated_time,
            "query_type_distribution": query_types,
            "average_priority": sum(sq.priority for sq in query_plan.sub_queries) / total_queries if total_queries > 0 else 0
        }


# 全局查询分解器实例
_query_decomposer: Optional[QueryDecomposer] = None


def get_query_decomposer(llm_provider: Optional[LLMProvider] = None) -> QueryDecomposer:
    """获取全局查询分解器实例"""
    global _query_decomposer
    if _query_decomposer is None:
        _query_decomposer = QueryDecomposer(llm_provider)
    return _query_decomposer


def reset_query_decomposer():
    """重置查询分解器（用于测试）"""
    global _query_decomposer
    _query_decomposer = None