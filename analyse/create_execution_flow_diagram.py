#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建MindSearchAgent执行流程可视化图

基于Terminal#1-190的执行日志，创建详细的执行流程图
"""

import sys
import os
from typing import Dict, List, Tuple

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.patches import FancyBboxPatch, ConnectionPatch
    import numpy as np
    HAS_VISUALIZATION = True
except ImportError:
    print("❌ 缺少可视化依赖，请安装: pip install matplotlib")
    HAS_VISUALIZATION = False
    sys.exit(1)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_execution_flow_diagram():
    """创建执行流程图"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # 定义颜色
    colors = {
        'user': '#E3F2FD',      # 浅蓝色
        'analysis': '#FFF3E0',   # 浅橙色
        'graph': '#E8F5E8',      # 浅绿色
        'search': '#F3E5F5',     # 浅紫色
        'success': '#C8E6C9',    # 成功绿色
        'failed': '#FFCDD2',     # 失败红色
        'result': '#FFECB3',     # 结果黄色
        'error': '#FF5252'       # 错误红色
    }
    
    # 绘制流程步骤
    steps = [
        # (x, y, width, height, text, color, step_num)
        (1, 10.5, 8, 0.8, "🤔 用户查询: 什么是人工智能？它有哪些应用领域？", colors['user'], "1"),
        (1, 9.5, 8, 0.6, "📊 状态: 正在分析查询...", colors['analysis'], "2"),
        (1, 8.7, 8, 0.6, "📊 状态: 创建搜索图...", colors['analysis'], "3"),
        (1, 7.9, 8, 0.6, "📊 状态: 开始搜索信息...", colors['analysis'], "4"),
        (1, 7.1, 8, 0.6, "🔗 图已创建: 5 个节点, 5 条边", colors['graph'], "5"),
    ]
    
    # 绘制基本流程步骤
    for x, y, w, h, text, color, step_num in steps:
        box = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor='gray',
            linewidth=1
        )
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=10, weight='bold')
        # 添加步骤编号
        circle = plt.Circle((x - 0.3, y + h/2), 0.15, color='steelblue', zorder=10)
        ax.add_patch(circle)
        ax.text(x - 0.3, y + h/2, step_num, ha='center', va='center', color='white', fontsize=8, weight='bold')
    
    # 绘制并行搜索部分
    # 成功的搜索节点
    success_box = FancyBboxPatch(
        (0.5, 5.5), 4, 1.2,
        boxstyle="round,pad=0.1",
        facecolor=colors['success'],
        edgecolor='green',
        linewidth=2
    )
    ax.add_patch(success_box)
    success_text = """🔍 子查询1: 人工智能的定义
节点ID: c32fe1b1-efee-4d10-b58c-3db4acd248ed
✅ 状态: COMPLETED
📊 结果: 5个引用，详细分析"""
    ax.text(2.5, 6.1, success_text, ha='center', va='center', fontsize=9)
    
    # 失败的搜索节点
    failed_box = FancyBboxPatch(
        (5.5, 5.5), 4, 1.2,
        boxstyle="round,pad=0.1",
        facecolor=colors['failed'],
        edgecolor='red',
        linewidth=2
    )
    ax.add_patch(failed_box)
    failed_text = """🔍 子查询2: 应用领域
节点ID: 5bc23b9a-f214-499c-b5f7-b63bce609226
❌ 状态: FAILED
🚨 错误: SSL连接失败"""
    ax.text(7.5, 6.1, failed_text, ha='center', va='center', fontsize=9)
    
    # 添加步骤编号
    circle1 = plt.Circle((0.2, 6.1), 0.15, color='green', zorder=10)
    ax.add_patch(circle1)
    ax.text(0.2, 6.1, "6a", ha='center', va='center', color='white', fontsize=8, weight='bold')
    
    circle2 = plt.Circle((5.2, 6.1), 0.15, color='red', zorder=10)
    ax.add_patch(circle2)
    ax.text(5.2, 6.1, "6b", ha='center', va='center', color='white', fontsize=8, weight='bold')
    
    # 错误详情框
    error_box = FancyBboxPatch(
        (5.5, 3.8), 4, 1.4,
        boxstyle="round,pad=0.1",
        facecolor=colors['error'],
        edgecolor='darkred',
        linewidth=2,
        alpha=0.8
    )
    ax.add_patch(error_box)
    error_text = """🚨 详细错误信息:
ssl.SSLError: [SSL] record layer failure
aiohttp.ClientConnectionError
⚠️ 资源泄漏:
Unclosed client session
Unclosed connector"""
    ax.text(7.5, 4.5, error_text, ha='center', va='center', fontsize=8, color='white')
    
    # 结果生成部分
    result_steps = [
        (1, 2.8, 8, 0.6, "📊 状态: 正在生成答案...", colors['analysis'], "7"),
        (1, 2.0, 8, 0.6, "💬 生成答案中... (1683 字符)", colors['result'], "8"),
        (1, 1.2, 8, 0.6, "🎉 搜索完成!", colors['success'], "9"),
    ]
    
    for x, y, w, h, text, color, step_num in result_steps:
        box = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor='gray',
            linewidth=1
        )
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=10, weight='bold')
        # 添加步骤编号
        circle = plt.Circle((x - 0.3, y + h/2), 0.15, color='steelblue', zorder=10)
        ax.add_patch(circle)
        ax.text(x - 0.3, y + h/2, step_num, ha='center', va='center', color='white', fontsize=8, weight='bold')
    
    # 绘制连接线
    # 主流程连接线
    main_connections = [
        ((5, 10.5), (5, 9.5)),  # 1->2
        ((5, 9.5), (5, 8.7)),   # 2->3
        ((5, 8.7), (5, 7.9)),   # 3->4
        ((5, 7.9), (5, 7.1)),   # 4->5
        ((5, 7.1), (2.5, 6.7)), # 5->6a
        ((5, 7.1), (7.5, 6.7)), # 5->6b
        ((2.5, 5.5), (3, 3.4)), # 6a->7
        ((7.5, 5.5), (7, 3.4)), # 6b->7
        ((5, 2.8), (5, 2.0)),   # 7->8
        ((5, 2.0), (5, 1.2)),   # 8->9
    ]
    
    for start, end in main_connections:
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))
    
    # 错误连接线
    ax.annotate('', xy=(7.5, 3.8), xytext=(7.5, 5.5),
               arrowprops=dict(arrowstyle='->', lw=2, color='red', linestyle='dashed'))
    
    # 添加标题和统计信息
    ax.text(5, 11.7, "MindSearchAgent 执行流程详细分析", ha='center', va='center', 
           fontsize=16, weight='bold')
    ax.text(5, 11.3, "基于 Terminal#1-190 执行日志", ha='center', va='center', 
           fontsize=12, style='italic')
    
    # 添加统计信息框
    stats_box = FancyBboxPatch(
        (0.5, 0.2), 9, 0.8,
        boxstyle="round,pad=0.1",
        facecolor='#F5F5F5',
        edgecolor='black',
        linewidth=1
    )
    ax.add_patch(stats_box)
    stats_text = """📊 执行统计: 节点总数: 5 | 边总数: 5 | 成功率: 40% | 完成节点: 2 | 失败节点: 3
📝 最终输出: 完整的AI定义和应用分析 (1683字符) + 5个参考文献"""
    ax.text(5, 0.6, stats_text, ha='center', va='center', fontsize=10, weight='bold')
    
    plt.tight_layout()
    return fig

def create_graph_structure_diagram():
    """创建图结构图"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # 节点位置和信息
    nodes = {
        'root': (5, 7, '🔵 ROOT\n原始查询', '#87CEEB', 'COMPLETED'),
        'search_q1': (2, 5.5, '🟢 SEARCH_Q1\n人工智能的定义', '#90EE90', 'COMPLETED'),
        'search_q2': (5, 5.5, '🟡 SEARCH_Q2\n历史发展', '#FFFF99', 'PENDING'),
        'search_q3': (8, 5.5, '🔴 SEARCH_Q3\n应用领域', '#FFB6C1', 'FAILED'),
        'result': (5, 3.5, '🟠 RESULT\n汇总结果', '#FFA500', 'PENDING'),
        'end': (5, 2, '🟣 END\n搜索完成', '#DDA0DD', 'PENDING')
    }
    
    # 绘制节点
    for node_id, (x, y, text, color, status) in nodes.items():
        # 根据状态调整边框
        edge_color = {
            'COMPLETED': 'green',
            'FAILED': 'red',
            'PENDING': 'gray',
            'RUNNING': 'orange'
        }.get(status, 'gray')
        
        edge_width = 3 if status in ['COMPLETED', 'FAILED'] else 1
        
        circle = plt.Circle((x, y), 0.6, facecolor=color, edgecolor=edge_color, linewidth=edge_width)
        ax.add_patch(circle)
        ax.text(x, y, text, ha='center', va='center', fontsize=9, weight='bold')
        
        # 添加状态标签
        status_color = {
            'COMPLETED': 'green',
            'FAILED': 'red',
            'PENDING': 'gray',
            'RUNNING': 'orange'
        }.get(status, 'gray')
        
        ax.text(x, y-1, status, ha='center', va='center', fontsize=8, 
               color=status_color, weight='bold')
    
    # 绘制边
    edges = [
        ('root', 'search_q1'),
        ('search_q1', 'search_q2'),
        ('search_q1', 'search_q3'),
        ('search_q1', 'result'),
        ('search_q2', 'result'),
        ('search_q3', 'result'),
        ('result', 'end')
    ]
    
    for start, end in edges:
        start_pos = nodes[start][:2]
        end_pos = nodes[end][:2]
        
        # 计算箭头位置（避开圆形节点）
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        length = np.sqrt(dx**2 + dy**2)
        
        if length > 0:
            # 标准化方向向量
            dx_norm = dx / length
            dy_norm = dy / length
            
            # 调整起点和终点（避开圆形）
            start_adjusted = (start_pos[0] + 0.6 * dx_norm, start_pos[1] + 0.6 * dy_norm)
            end_adjusted = (end_pos[0] - 0.6 * dx_norm, end_pos[1] - 0.6 * dy_norm)
            
            ax.annotate('', xy=end_adjusted, xytext=start_adjusted,
                       arrowprops=dict(arrowstyle='->', lw=2, color='darkblue'))
    
    # 添加标题
    ax.text(5, 7.8, "搜索图结构 (6个节点, 7条边)", ha='center', va='center', 
           fontsize=14, weight='bold')
    
    # 添加图例
    legend_elements = [
        ('🔵 ROOT', '#87CEEB'),
        ('🟢 SEARCH', '#90EE90'),
        ('🟠 RESULT', '#FFA500'),
        ('🟣 END', '#DDA0DD')
    ]
    
    for i, (label, color) in enumerate(legend_elements):
        x_pos = 0.5 + i * 2.3
        circle = plt.Circle((x_pos, 0.5), 0.2, facecolor=color, edgecolor='black')
        ax.add_patch(circle)
        ax.text(x_pos, 0.1, label, ha='center', va='center', fontsize=8)
    
    plt.tight_layout()
    return fig

def main():
    """主函数"""
    print("🎨 创建MindSearchAgent执行流程可视化图")
    
    if not HAS_VISUALIZATION:
        return
    
    try:
        # 创建执行流程图
        print("📊 创建执行流程图...")
        flow_fig = create_execution_flow_diagram()
        flow_fig.savefig('mindsearch_execution_flow.png', dpi=300, bbox_inches='tight')
        print("✅ 执行流程图已保存: mindsearch_execution_flow.png")
        
        # 创建图结构图
        print("📊 创建图结构图...")
        graph_fig = create_graph_structure_diagram()
        graph_fig.savefig('mindsearch_graph_structure.png', dpi=300, bbox_inches='tight')
        print("✅ 图结构图已保存: mindsearch_graph_structure.png")
        
        print("\n🎉 所有图表创建完成！")
        print("\n生成的文件:")
        print("  - mindsearch_execution_flow.png (详细执行流程)")
        print("  - mindsearch_graph_structure.png (图结构展示)")
        print("  - execution_flow_analysis.md (详细分析文档)")
        
        # 显示图表（如果在支持的环境中）
        try:
            plt.show()
        except:
            print("\n💡 提示: 图片已保存，请查看生成的PNG文件")
            
    except Exception as e:
        print(f"❌ 创建图表时出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()