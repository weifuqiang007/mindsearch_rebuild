#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图状态管理的 MindSearchAgent
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from agents.mindsearch_agent import MindSearchAgent, LLMProvider
except ImportError:
    # 如果导入失败，尝试添加项目根目录到路径
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    from langchain_rebuild.agents.mindsearch_agent import MindSearchAgent, LLMProvider


def print_callback(data):
    """打印回调函数"""
    msg_type = data.get('type', 'unknown')
    msg_data = data.get('data', {})
    
    if msg_type == 'status':
        print(f"📊 状态: {msg_data.get('message', '')}")
    elif msg_type == 'graph_created':
        graph_data = msg_data
        print(f"🔗 图已创建: {len(graph_data.get('nodes', {}))} 个节点, {len(graph_data.get('edges', {}))} 条边")
    elif msg_type == 'sub_query_start':
        print(f"🔍 开始子查询: {msg_data.get('query', '')} (节点: {msg_data.get('node_id', '')})")
    elif msg_type == 'sub_query_complete':
        print(f"✅ 子查询完成: {msg_data.get('query', '')}")
    elif msg_type == 'node_updated':
        print(f"🔄 节点更新: {msg_data.get('node_id', '')} -> {msg_data.get('status', '')}")
    elif msg_type == 'graph_complete':
        print(f"🎯 图执行完成")
    elif msg_type == 'answer_chunk':
        # 流式答案，只显示进度
        content = msg_data.get('content', '')
        print(f"\r💬 生成答案中... ({len(content)} 字符)", end='', flush=True)
    elif msg_type == 'complete':
        print("\n🎉 搜索完成!")
    elif msg_type == 'error':
        print(f"❌ 错误: {msg_data.get('error', '')}")


async def test_graph_search():
    """测试图搜索功能"""
    print("=== 测试图状态管理的 MindSearchAgent ===")
    
    # 创建智能体
    agent = MindSearchAgent(
        llm_provider=LLMProvider.SILICONFLOW,
        max_search_steps=3,
        max_results_per_search=5
    )
    
    # 测试查询
    query = "什么是人工智能？它有哪些应用领域？"
    print(f"\n🤔 查询: {query}")
    print("-" * 50)
    
    try:
        # 执行搜索
        session = await agent.asearch(query, callback_func=print_callback)
        
        print("\n" + "=" * 50)
        print("📋 搜索结果摘要:")
        print(f"会话ID: {session.session_id}")
        print(f"原始查询: {session.original_query}")
        print(f"搜索步骤数: {len(session.search_steps)}")
        print(f"总引用数: {len(session.total_references)}")
        
        # 显示查询计划
        if session.query_plan:
            print(f"\n📝 查询计划:")
            for i, sub_query in enumerate(session.query_plan.sub_queries, 1):
                print(f"  {i}. {sub_query.query}")
                if sub_query.dependencies:
                    print(f"     依赖: {sub_query.dependencies}")
        
        # 显示搜索步骤
        print(f"\n🔍 搜索步骤:")
        for i, step in enumerate(session.search_steps, 1):
            print(f"  {i}. {step.query}")
            print(f"     结果数: {len(step.search_results)}")
            print(f"     引用数: {len(step.references)}")
            print(f"     分析: {step.analysis[:100]}..." if len(step.analysis) > 100 else f"     分析: {step.analysis}")
        
        # 显示图统计信息
        stats = agent.get_session_statistics(session)
        if 'graph_statistics' in stats:
            graph_stats = stats['graph_statistics']
            print(f"\n📊 图执行统计:")
            print(f"  节点总数: {graph_stats['total_nodes']}")
            print(f"  边总数: {graph_stats['total_edges']}")
            print(f"  成功率: {graph_stats['success_rate']:.2%}")
            print(f"  失败节点: {graph_stats['failed_nodes']}")
            print(f"  节点状态分布: {graph_stats['node_status_distribution']}")
        
        # 显示最终答案
        print(f"\n💡 最终答案:")
        print(session.final_answer)
        
        print("\n" + "=" * 50)
        print("✅ 测试完成!")
        
        return session
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_graph_structure():
    """测试图结构的创建"""
    print("\n=== 测试图结构创建 ===")
    
    try:
        from core.query_decomposer import QueryPlan, SubQuery, QueryType
    except ImportError:
        # 如果导入失败，尝试相对导入
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from core.query_decomposer import QueryPlan, SubQuery, QueryType
    
    # 创建模拟查询计划
    query_plan = QueryPlan(
        original_query="什么是人工智能？",
        sub_queries=[
            SubQuery(
                id="q1", 
                query="人工智能的定义", 
                query_type=QueryType.FACTUAL,
                priority=1,
                dependencies=[],
                keywords=["人工智能", "定义"],
                expected_sources=["学术", "百科"]
            ),
            SubQuery(
                id="q2", 
                query="人工智能的历史发展", 
                query_type=QueryType.TEMPORAL,
                priority=2,
                dependencies=["q1"],
                keywords=["人工智能", "历史", "发展"],
                expected_sources=["学术", "历史"]
            ),
            SubQuery(
                id="q3", 
                query="人工智能的应用领域", 
                query_type=QueryType.FACTUAL,
                priority=2,
                dependencies=["q1"],
                keywords=["人工智能", "应用", "领域"],
                expected_sources=["技术", "商业"]
            )
        ],
        execution_order=[["q1"], ["q2", "q3"]],
        estimated_time=30
    )
    
    # 创建智能体并生成图
    agent = MindSearchAgent(llm_provider=LLMProvider.SILICONFLOW)
    graph = agent._create_search_graph(query_plan)
    
    print(f"图节点数: {len(graph.nodes)}")
    print(f"图边数: {len(graph.edges)}")
    
    print("\n节点信息:")
    for node_id, node in graph.nodes.items():
        print(f"  {node.name} ({node.node_type.value}): {node.content}")
    
    print("\n边信息:")
    for edge_id, edge in graph.edges.items():
        from_node = graph.nodes[edge.from_node].name
        to_node = graph.nodes[edge.to_node].name
        print(f"  {from_node} -> {to_node}")
    
    print("\n可执行节点:")
    ready_nodes = graph.get_ready_nodes()
    for node_id in ready_nodes:
        node = graph.nodes[node_id]
        print(f"  {node.name} ({node.node_type.value})")


if __name__ == "__main__":
    # 测试图结构
    test_graph_structure()
    
    # 测试完整搜索流程
    asyncio.run(test_graph_search())