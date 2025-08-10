#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MindSearchAgent 图可视化示例

这个示例展示了如何使用 MindSearchAgent 的图可视化功能来直观地查看搜索图的结构和执行状态。

功能包括：
1. 图形化可视化（使用 matplotlib 和 networkx）
2. 文本结构打印
3. DOT 格式导出

使用前请确保安装依赖：
pip install matplotlib networkx
"""

import sys
import os
from typing import Optional

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from agents.mindsearch_agent import MindSearchAgent
    from core.search_manager import SearchManager
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在正确的项目目录中运行此脚本")
    sys.exit(1)

def create_test_agent() -> MindSearchAgent:
    """创建测试用的 MindSearchAgent"""
    # 创建搜索管理器（使用模拟配置）
    search_manager = SearchManager()
    
    # 创建 MindSearchAgent
    agent = MindSearchAgent(
        search_manager=search_manager,
        max_iterations=3,
        enable_graph_search=True  # 启用图搜索功能
    )
    
    return agent

def print_callback(callback_type: str, data: dict):
    """回调函数，用于打印搜索过程中的信息"""
    if callback_type == "graph_created":
        print(f"📊 图已创建: {data.get('nodes', 0)} 个节点, {data.get('edges', 0)} 条边")
    elif callback_type == "node_completed":
        print(f"✅ 节点完成: {data.get('node_name', 'Unknown')}")
    elif callback_type == "node_failed":
        print(f"❌ 节点失败: {data.get('node_name', 'Unknown')} - {data.get('error', 'Unknown error')}")
    elif callback_type == "search_completed":
        print(f"🎉 搜索完成")

def example_1_basic_visualization():
    """示例1: 基本的图可视化"""
    print("\n" + "="*60)
    print("示例1: 基本的图可视化")
    print("="*60)
    
    # 创建代理
    agent = create_test_agent()
    agent.callback_func = print_callback
    
    # 执行一个复杂查询来生成图
    query = "人工智能在医疗领域的应用现状和发展趋势是什么？"
    print(f"🔍 执行查询: {query}")
    
    try:
        # 执行搜索（这会创建和执行图）
        result = agent.search(query)
        print(f"\n📝 搜索结果摘要: {result[:200]}...")
        
        # 打印图的文本结构
        print("\n📋 图结构概览:")
        agent.print_search_graph()
        
        # 显示图的可视化
        print("\n🎨 显示图可视化...")
        agent.visualize_search_graph(
            title="AI医疗应用搜索图",
            figsize=(14, 10)
        )
        
        # 保存图片
        print("\n💾 保存图片到 'search_graph_example1.png'")
        agent.visualize_search_graph(
            save_path="search_graph_example1.png",
            title="AI医疗应用搜索图"
        )
        
        # 导出 DOT 格式
        print("\n📄 导出 DOT 格式到 'search_graph_example1.dot'")
        agent.export_graph_dot("search_graph_example1.dot")
        
        # 显示统计信息
        stats = agent.get_graph_statistics()
        print(f"\n📊 图执行统计:")
        print(f"   总节点数: {stats.get('total_nodes', 0)}")
        print(f"   完成节点数: {stats.get('completed_nodes', 0)}")
        print(f"   失败节点数: {stats.get('failed_nodes', 0)}")
        print(f"   成功率: {stats.get('success_rate', 0):.2%}")
        print(f"   执行时间: {stats.get('execution_time', 0):.2f}秒")
        
    except Exception as e:
        print(f"❌ 执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

def example_2_custom_visualization():
    """示例2: 自定义可视化选项"""
    print("\n" + "="*60)
    print("示例2: 自定义可视化选项")
    print("="*60)
    
    # 创建代理
    agent = create_test_agent()
    agent.callback_func = print_callback
    
    # 执行一个简单查询
    query = "Python编程语言的特点"
    print(f"🔍 执行查询: {query}")
    
    try:
        # 执行搜索
        result = agent.search(query)
        print(f"\n📝 搜索结果摘要: {result[:150]}...")
        
        # 自定义可视化选项
        print("\n🎨 自定义可视化选项...")
        agent.visualize_search_graph(
            save_path="search_graph_custom.png",
            show_labels=True,
            figsize=(16, 12),
            title="Python特点搜索图 - 自定义样式"
        )
        
        print("✅ 自定义图片已保存到 'search_graph_custom.png'")
        
    except Exception as e:
        print(f"❌ 执行过程中出现错误: {e}")

def example_3_multiple_queries():
    """示例3: 多个查询的图比较"""
    print("\n" + "="*60)
    print("示例3: 多个查询的图比较")
    print("="*60)
    
    queries = [
        "机器学习的基本概念",
        "深度学习在计算机视觉中的应用",
        "自然语言处理的发展历程和未来趋势"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 查询 {i}: {query}")
        
        # 创建新的代理实例
        agent = create_test_agent()
        agent.callback_func = print_callback
        
        try:
            # 执行搜索
            result = agent.search(query)
            
            # 保存对应的可视化图
            filename = f"search_graph_query_{i}.png"
            agent.visualize_search_graph(
                save_path=filename,
                title=f"查询{i}: {query[:20]}...",
                figsize=(12, 8)
            )
            
            # 获取统计信息
            stats = agent.get_graph_statistics()
            print(f"   📊 节点数: {stats.get('total_nodes', 0)}, 成功率: {stats.get('success_rate', 0):.2%}")
            print(f"   💾 图片已保存: {filename}")
            
        except Exception as e:
            print(f"   ❌ 查询失败: {e}")

def main():
    """主函数"""
    print("🚀 MindSearchAgent 图可视化示例")
    print("\n这个示例将展示如何使用图可视化功能来直观地查看搜索过程")
    
    # 检查可视化依赖
    try:
        import matplotlib.pyplot as plt
        import networkx as nx
        print("✅ 可视化依赖已安装")
    except ImportError as e:
        print(f"❌ 缺少可视化依赖: {e}")
        print("请运行: pip install matplotlib networkx")
        return
    
    try:
        # 运行示例
        example_1_basic_visualization()
        example_2_custom_visualization()
        example_3_multiple_queries()
        
        print("\n" + "="*60)
        print("🎉 所有示例执行完成！")
        print("\n生成的文件:")
        print("  - search_graph_example1.png (基本可视化)")
        print("  - search_graph_example1.dot (DOT格式)")
        print("  - search_graph_custom.png (自定义样式)")
        print("  - search_graph_query_1.png (查询1)")
        print("  - search_graph_query_2.png (查询2)")
        print("  - search_graph_query_3.png (查询3)")
        print("\n💡 提示: 你可以使用以下方法在代码中调用可视化:")
        print("  agent.visualize_search_graph()  # 显示图")
        print("  agent.print_search_graph()      # 打印文本结构")
        print("  agent.export_graph_dot()        # 导出DOT格式")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n⏹️  用户中断执行")
    except Exception as e:
        print(f"\n❌ 执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()