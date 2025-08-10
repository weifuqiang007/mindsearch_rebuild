#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图可视化功能测试脚本

这个脚本用于快速测试图可视化功能是否正常工作。
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from core.simple_graph import SimpleSearchGraph, NodeType, NodeStatus
    from core.query_decomposer import QueryPlan, SubQuery, QueryType
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("尝试动态导入...")
    try:
        # 动态调整路径
        sys.path.insert(0, os.path.join(project_root, 'core'))
        from simple_graph import SimpleSearchGraph, NodeType, NodeStatus
        from query_decomposer import QueryPlan, SubQuery, QueryType
        print("✅ 动态导入成功")
    except ImportError as e2:
        print(f"❌ 动态导入也失败: {e2}")
        sys.exit(1)

def create_search_graph(query_plan) -> SimpleSearchGraph:
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

def test_graph_visualization():
    """测试图可视化功能"""
    print("🧪 测试图可视化功能")
    print("="*50)
    
    # 检查可视化依赖
    try:
        import matplotlib.pyplot as plt
        import networkx as nx
        print("✅ 可视化依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少可视化依赖: {e}")
        print("请运行: pip install matplotlib networkx")
        return False
    
    # 创建测试查询计划
    sub_queries = [
        SubQuery(
            id="sq_1",
            query="人工智能的定义",
            query_type=QueryType.FACTUAL,
            priority=1,
            dependencies=[],
            keywords=["人工智能", "定义", "概念"],
            expected_sources=["学术文献", "百科全书"]
        ),
        SubQuery(
            id="sq_2",
            query="机器学习算法分类",
            query_type=QueryType.ANALYTICAL,
            priority=2,
            dependencies=["sq_1"],
            keywords=["机器学习", "算法", "分类"],
            expected_sources=["技术文档", "学术论文"]
        ),
        SubQuery(
            id="sq_3",
            query="深度学习应用案例",
            query_type=QueryType.COMPARATIVE,
            priority=3,
            dependencies=["sq_2"],
            keywords=["深度学习", "应用", "案例"],
            expected_sources=["行业报告", "案例研究"]
        ),
        SubQuery(
            id="sq_4",
            query="AI发展趋势预测",
            query_type=QueryType.ANALYTICAL,
            priority=4,
            dependencies=["sq_1", "sq_3"],
            keywords=["AI", "发展趋势", "预测"],
            expected_sources=["研究报告", "专家观点"]
        )
    ]
    
    query_plan = QueryPlan(
        original_query="人工智能技术发展现状和趋势",
        sub_queries=sub_queries,
        execution_order=[["sq_1"], ["sq_2"], ["sq_3"], ["sq_4"]],
        estimated_time=300
    )
    
    # 创建搜索图
    print("\n📊 创建搜索图...")
    graph = create_search_graph(query_plan)
    
    print(f"✅ 图创建成功: {len(graph.nodes)} 个节点, {len(graph.edges)} 条边")
    
    # 模拟执行一些节点
    print("\n🔄 模拟节点执行...")
    nodes = list(graph.nodes.values())
    
    # 执行第一个节点（成功）
    if len(nodes) > 0:
        graph.update_node_status(nodes[0].name, NodeStatus.RUNNING)
        graph.update_node_status(nodes[0].name, NodeStatus.COMPLETED, result="AI是模拟人类智能的技术")
        print(f"✅ 节点 '{nodes[0].name}' 执行成功")
    
    # 执行第二个节点（成功）
    if len(nodes) > 1:
        graph.update_node_status(nodes[1].name, NodeStatus.RUNNING)
        graph.update_node_status(nodes[1].name, NodeStatus.COMPLETED, result="包括监督学习、无监督学习等")
        print(f"✅ 节点 '{nodes[1].name}' 执行成功")
    
    # 执行第三个节点（失败）
    if len(nodes) > 2:
        graph.update_node_status(nodes[2].name, NodeStatus.RUNNING)
        graph.update_node_status(nodes[2].name, NodeStatus.FAILED, error="网络连接超时")
        print(f"❌ 节点 '{nodes[2].name}' 执行失败")
    
    # 测试文本结构打印
    print("\n📋 打印图结构:")
    graph.print_graph_structure()
    
    # 测试图可视化
    print("\n🎨 测试图可视化...")
    try:
        # 显示图（如果在支持的环境中）
        graph.visualize_graph(
            save_path="test_graph_visualization.png",
            title="测试搜索图",
            figsize=(12, 8)
        )
        print("✅ 图片已保存到 'test_graph_visualization.png'")
    except Exception as e:
        print(f"❌ 图可视化失败: {e}")
        return False
    
    # 测试 DOT 导出
    print("\n📄 测试 DOT 导出...")
    try:
        graph.export_dot("test_graph.dot")
        print("✅ DOT 文件已保存到 'test_graph.dot'")
    except Exception as e:
        print(f"❌ DOT 导出失败: {e}")
        return False
    
    print("\n🎉 所有可视化功能测试通过！")
    return True

def main():
    """主函数"""
    print("🚀 图可视化功能测试")
    print("\n这个测试将验证图可视化的各项功能是否正常工作")
    
    try:
        success = test_graph_visualization()
        
        if success:
            print("\n" + "="*50)
            print("✅ 测试完成！生成的文件:")
            print("  - test_graph_visualization.png (可视化图片)")
            print("  - test_graph.dot (DOT格式文件)")
            print("\n💡 现在你可以在 MindSearchAgent 中使用以下方法:")
            print("  agent.visualize_search_graph()  # 显示/保存图片")
            print("  agent.print_search_graph()      # 打印文本结构")
            print("  agent.export_graph_dot()        # 导出DOT格式")
        else:
            print("\n❌ 测试失败，请检查错误信息")
            
    except KeyboardInterrupt:
        print("\n⏹️  用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()