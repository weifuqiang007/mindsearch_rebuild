#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MindSearchAgent 图状态管理功能使用示例

这个示例展示了如何使用带有图状态管理功能的 MindSearchAgent 进行复杂查询。
图状态管理提供了以下优势：
1. 可视化查询执行流程
2. 并行执行独立的子查询
3. 智能依赖管理
4. 详细的执行统计
5. 错误处理和恢复
"""

import asyncio
import sys
import os
from typing import Dict, Any
from datetime import datetime
import io
from contextlib import redirect_stdout



# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 添加项目根目录到路径以确保正确导入
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from core.llm_manager import LLMProvider
    from agents.mindsearch_agent import MindSearchAgent
    from core.search_tools import SearchToolManager
    from core.simple_graph import NodeStatus
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的项目目录中运行此脚本")
    sys.exit(1)


# 全局变量用于收集输出
output_buffer = []

def log_output(message: str):
    """记录输出到缓冲区"""
    output_buffer.append(message)
    print(message)  # 同时输出到控制台

def print_callback(message: str, **kwargs):
    """回调函数，用于打印搜索进度"""
    msg = f"📢 {message}"
    log_output(msg)
    if kwargs:
        for key, value in kwargs.items():
            log_output(f"   {key}: {value}")


def print_graph_statistics(stats: Dict[str, Any]):
    """打印图执行统计信息"""
    log_output("\n📊 图执行统计:")
    
    if 'graph_stats' in stats:
        graph_stats = stats['graph_stats']
        log_output(f"  总节点数: {graph_stats.get('total_nodes', 0)}")
        log_output(f"  已完成节点: {graph_stats.get('completed_nodes', 0)}")
        log_output(f"  失败节点: {graph_stats.get('failed_nodes', 0)}")
        log_output(f"  成功率: {graph_stats.get('success_rate', 0):.2%}")
        log_output(f"  执行时间: {graph_stats.get('execution_time', 0):.2f}秒")
        
        if 'node_details' in graph_stats:
            log_output("\n  节点详情:")
            for node_name, node_info in graph_stats['node_details'].items():
                status_emoji = {
                    NodeStatus.COMPLETED.value: "✅",
                    NodeStatus.FAILED.value: "❌",
                    NodeStatus.RUNNING.value: "🔄",
                    NodeStatus.PENDING.value: "⏳"
                }.get(node_info.get('status', ''), "❓")
                
                log_output(f"    {status_emoji} {node_name}: {node_info.get('status', 'unknown')}")
                if node_info.get('error'):
                    log_output(f"      错误: {node_info['error']}")


async def example_complex_query():
    """复杂查询示例：人工智能相关的多维度查询"""
    log_output("=== 复杂查询示例：人工智能的发展与应用 ===")
    
    # 创建搜索管理器（这里使用模拟配置）
    search_manager = SearchToolManager()

    # 创建 MindSearchAgent
    agent = MindSearchAgent(
        llm_provider=LLMProvider.OPENAI,
        # search_manager=search_manager,
        max_search_steps=3,
        max_results_per_search=5
    )
    
    # 复杂查询
    query = "人工智能的发展历史、当前应用领域和未来趋势是什么？"
    
    log_output(f"🔍 查询: {query}\n")
    
    try:
        # 执行搜索（使用图状态管理）
        result = await agent.asearch(
            query=query,
            callback=print_callback
        )
        
        log_output("\n" + "="*50)
        log_output("🎯 搜索结果:")
        log_output(result)
        
        # 获取并显示统计信息
        stats = agent.get_session_statistics(session=result)
        print_graph_statistics(stats)
        
    except Exception as e:
        log_output(f"❌ 搜索过程中发生错误: {e}")
        
        # 即使出错也显示统计信息
        stats = agent.get_session_statistics(session=result)
        print_graph_statistics(stats)


async def example_simple_query():
    """简单查询示例"""
    log_output("\n=== 简单查询示例：Python编程 ===")
    
    # search_manager = SearchManager()
    search_manager = SearchToolManager()
    agent = MindSearchAgent(
        llm_provider=LLMProvider.SILICONFLOW,
        max_search_steps=3,
        max_results_per_search=5
    )
    
    query = "Python编程语言的特点和优势"
    log_output(f"🔍 查询: {query}\n")
    
    try:
        result = await agent.asearch(
            query=query,
            callback_func=print_callback
        )
        
        log_output("\n" + "="*50)
        log_output("🎯 搜索结果:")
        log_output(result)
        
        stats = agent.get_session_statistics(session=result)
        print_graph_statistics(stats)
        
    except Exception as e:
        log_output(f"❌ 搜索过程中发生错误: {e}")


async def example_graph_visualization():
    """图可视化示例"""
    log_output("\n=== 图可视化示例 ===")
    
    # search_manager = SearchManager()
    search_manager = SearchToolManager()
    agent = MindSearchAgent(
        llm_provider=LLMProvider.OPENAI,
        # search_manager=search_manager,
        max_search_steps=3,
        max_results_per_search=5
    )
    
    query = "机器学习的基本概念、算法分类和实际应用"
    log_output(f"🔍 查询: {query}\n")
    
    # 定义详细的回调函数
    def detailed_callback(message: str, **kwargs):
        log_output(f"📢 {message}")
        
        # 如果有图相关信息，显示图状态
        if 'graph' in kwargs:
            graph = kwargs['graph']
            ready_nodes = graph.get_ready_nodes()
            if ready_nodes:
                node_names = [graph.nodes[nid].name for nid in ready_nodes]
                log_output(f"   可执行节点: {', '.join(node_names)}")
        
        # 显示其他信息
        for key, value in kwargs.items():
            if key != 'graph':  # 避免打印整个图对象
                log_output(f"   {key}: {value}")
    
    try:
        result = await agent.asearch(
            query=query,
            callback=detailed_callback
        )
        
        log_output("\n" + "="*50)
        log_output("🎯 搜索结果:")
        log_output(result)
        
        # 获取图统计信息
        stats = agent.get_session_statistics(session=result)
        print_graph_statistics(stats)
        
        # 显示图结构信息
        if hasattr(agent, '_current_graph') and agent._current_graph:
            graph = agent._current_graph
            log_output("\n🔗 图结构概览:")
            log_output(f"  节点总数: {len(graph.nodes)}")
            log_output(f"  边总数: {len(graph.edges)}")
            
            # 按类型统计节点
            from collections import defaultdict
            node_types = defaultdict(int)
            for node in graph.nodes.values():
                node_types[node.node_type.value] += 1
            
            log_output("  节点类型分布:")
            for node_type, count in node_types.items():
                log_output(f"    {node_type}: {count}")
        
    except Exception as e:
        log_output(f"❌ 搜索过程中发生错误: {e}")


def print_usage_guide():
    """打印使用指南"""
    log_output("\n" + "="*60)
    log_output("📖 MindSearchAgent 图功能使用指南")
    log_output("="*60)
    log_output("""
🔧 主要功能:
  1. 自动查询分解 - 将复杂查询分解为多个子查询
  2. 图状态管理 - 使用有向无环图管理查询执行流程
  3. 并行执行 - 独立的子查询可以并行执行
  4. 依赖管理 - 自动处理子查询之间的依赖关系
  5. 错误处理 - 智能处理节点失败和依赖错误
  6. 执行统计 - 提供详细的执行统计和性能分析

🚀 使用步骤:
  1. 创建 SearchManager 实例
  2. 创建 MindSearchAgent 实例
  3. 调用 asearch() 方法执行查询
  4. 使用 callback 参数监控执行进度
  5. 通过 get_session_statistics() 获取统计信息

💡 最佳实践:
  - 为复杂查询设置合适的 max_sub_queries 参数
  - 使用回调函数监控长时间运行的查询
  - 定期检查统计信息以优化查询策略
  - 处理可能的异常情况

📊 图状态管理优势:
  - 可视化查询执行流程
  - 提高查询执行效率
  - 更好的错误处理和恢复
  - 详细的性能分析
""")


def save_output_to_markdown():
    """将输出保存到markdown文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"graph_search_example_output_{timestamp}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# MindSearchAgent 图状态管理功能演示输出\n\n")
        f.write(f"**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        for item in output_buffer:
            # 确保内容是字符串类型
            if isinstance(item, str):
                line = item
            else:
                line = str(item)
            
            # 处理markdown特殊字符
            line = line.replace('\n', '\n\n')
            f.write(line + '\n\n')
    
    log_output(f"\n📄 输出已保存到文件: {filename}")
    return filename


async def main():
    """主函数"""
    log_output("🚀 MindSearchAgent 图状态管理功能演示")
    log_output("="*50)
    
    # 打印使用指南
    print_usage_guide()
    
    # 运行示例
    # await example_complex_query()
    await example_simple_query()
    # await example_graph_visualization()
    
    log_output("\n🎉 所有示例执行完成！")
    log_output("\n💡 提示: 在实际使用中，请确保正确配置搜索引擎和API密钥。")
    
    # 保存输出到markdown文件
    filename = save_output_to_markdown()
    print(f"\n✅ 完整的执行过程已保存到: {filename}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())