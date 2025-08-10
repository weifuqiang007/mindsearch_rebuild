# -*- coding: utf-8 -*-
# 开发团队   ：tianyikeji
# 开发人员   ：weifuqiang
# 开发时间   ：2025/8/6  18:12 
# 文件名称   ：simple_graph.PY
# 开发工具   ：PyCharm


# core/simple_graph.py
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from enum import Enum
from datetime import datetime
import uuid
try:
    import matplotlib.pyplot as plt
    import networkx as nx
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False


class NodeType(Enum):
    ROOT = "root"
    SEARCH = "search"
    RESULT = "result"
    END = "end"


class NodeStatus(Enum):
    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 执行失败


@dataclass
class GraphNode:
    """图节点"""
    id: str
    name: str
    content: str
    node_type: NodeType
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "type": self.node_type.value,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class GraphEdge:
    """图边"""
    id: str
    from_node: str
    to_node: str
    weight: float = 1.0


class SimpleSearchGraph:
    """简化版搜索图"""

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.adjacency_list: Dict[str, List[str]] = {}
        self.execution_order: List[List[str]] = []  # 执行阶段

    def add_node(self, name: str, content: str, node_type: NodeType) -> str:
        """添加节点"""
        node_id = str(uuid.uuid4())
        node = GraphNode(
            id=node_id,
            name=name,
            content=content,
            node_type=node_type
        )
        self.nodes[node_id] = node
        self.adjacency_list[node_id] = []
        return node_id

    def add_edge(self, from_node_id: str, to_node_id: str) -> str:
        """添加边"""
        edge_id = str(uuid.uuid4())
        edge = GraphEdge(
            id=edge_id,
            from_node=from_node_id,
            to_node=to_node_id
        )
        self.edges[edge_id] = edge
        self.adjacency_list[from_node_id].append(to_node_id)
        return edge_id

    def get_ready_nodes(self) -> List[str]:
        """获取可以执行的节点（所有依赖都已完成）"""
        ready_nodes = []
        for node_id, node in self.nodes.items():
            if node.status == NodeStatus.PENDING:
                # 检查所有父节点是否都已完成
                parent_nodes = self.get_parent_nodes(node_id)
                if all(self.nodes[pid].status == NodeStatus.COMPLETED for pid in parent_nodes):
                    ready_nodes.append(node_id)
        return ready_nodes

    def get_parent_nodes(self, node_id: str) -> List[str]:
        """获取父节点"""
        parents = []
        for edge in self.edges.values():
            if edge.to_node == node_id:
                parents.append(edge.from_node)
        return parents

    def update_node_status(self, node_id: str, status: NodeStatus, result: Any = None, error: str = None):
        """更新节点状态"""
        if node_id in self.nodes:
            self.nodes[node_id].status = status
            self.nodes[node_id].updated_at = datetime.now()
            if result is not None:
                self.nodes[node_id].result = result
            if error is not None:
                self.nodes[node_id].error = error

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "edges": {eid: {"id": edge.id, "from": edge.from_node, "to": edge.to_node, "weight": edge.weight}
                      for eid, edge in self.edges.items()},
            "adjacency_list": self.adjacency_list,
            "execution_order": self.execution_order
        }
    
    def visualize_graph(self, save_path: Optional[str] = None, show_labels: bool = True, 
                       figsize: tuple = (12, 8), title: str = "搜索图结构") -> None:
        """可视化图结构
        
        Args:
            save_path: 保存图片的路径，如果为None则显示图片
            show_labels: 是否显示节点标签
            figsize: 图片大小
            title: 图片标题
        """
        if not HAS_VISUALIZATION:
            print("❌ 缺少可视化依赖库，请安装: pip install matplotlib networkx")
            return
        
        # 创建NetworkX图
        G = nx.DiGraph()
        
        # 添加节点
        for node_id, node in self.nodes.items():
            G.add_node(node_id, 
                      name=node.name,
                      node_type=node.node_type.value,
                      status=node.status.value)
        
        # 添加边
        for edge in self.edges.values():
            G.add_edge(edge.from_node, edge.to_node)
        
        # 创建图形
        plt.figure(figsize=figsize)
        plt.title(title, fontsize=16, fontweight='bold')
        
        # 使用层次布局
        try:
            pos = nx.spring_layout(G, k=3, iterations=50)
        except:
            pos = nx.random_layout(G)
        
        # 定义节点颜色映射
        node_colors = {
            NodeType.ROOT.value: '#FF6B6B',      # 红色
            NodeType.SEARCH.value: '#4ECDC4',    # 青色
            NodeType.RESULT.value: '#45B7D1',    # 蓝色
            NodeType.END.value: '#96CEB4'        # 绿色
        }
        
        # 定义状态颜色映射（边框）
        status_colors = {
            NodeStatus.PENDING.value: '#FFA500',     # 橙色
            NodeStatus.RUNNING.value: '#FFD700',     # 金色
            NodeStatus.COMPLETED.value: '#32CD32',   # 绿色
            NodeStatus.FAILED.value: '#DC143C'       # 深红色
        }
        
        # 绘制节点
        for node_id, node in self.nodes.items():
            node_color = node_colors.get(node.node_type.value, '#CCCCCC')
            edge_color = status_colors.get(node.status.value, '#000000')
            
            nx.draw_networkx_nodes(G, pos, 
                                 nodelist=[node_id],
                                 node_color=node_color,
                                 edgecolors=edge_color,
                                 linewidths=3,
                                 node_size=1500,
                                 alpha=0.8)
        
        # 绘制边
        nx.draw_networkx_edges(G, pos, 
                             edge_color='#666666',
                             arrows=True,
                             arrowsize=20,
                             arrowstyle='->',
                             width=2,
                             alpha=0.7)
        
        # 绘制标签
        if show_labels:
            labels = {node_id: node.name for node_id, node in self.nodes.items()}
            nx.draw_networkx_labels(G, pos, labels, 
                                  font_size=10,
                                  font_weight='bold',
                                  font_color='white')
        
        # 添加图例
        legend_elements = []
        
        # 节点类型图例
        for node_type, color in node_colors.items():
            legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                            markerfacecolor=color, markersize=10,
                                            label=f'{node_type}节点'))
        
        # 状态图例
        for status, color in status_colors.items():
            legend_elements.append(plt.Line2D([0], [0], marker='o', color=color, 
                                            markerfacecolor='w', markersize=8,
                                            label=f'{status}状态', markeredgewidth=2))
        
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
        
        # 设置图形属性
        plt.axis('off')
        plt.tight_layout()
        
        # 保存或显示
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 图结构已保存到: {save_path}")
        else:
            plt.show()
    
    def print_graph_structure(self) -> None:
        """打印图结构的文本表示"""
        print("\n📊 图结构概览:")
        print(f"  节点总数: {len(self.nodes)}")
        print(f"  边总数: {len(self.edges)}")
        
        # 按类型统计节点
        from collections import defaultdict
        node_type_count = defaultdict(int)
        status_count = defaultdict(int)
        
        for node in self.nodes.values():
            node_type_count[node.node_type.value] += 1
            status_count[node.status.value] += 1
        
        print("\n  节点类型分布:")
        for node_type, count in node_type_count.items():
            print(f"    {node_type}: {count}")
        
        print("\n  节点状态分布:")
        for status, count in status_count.items():
            emoji = {
                NodeStatus.PENDING.value: "⏳",
                NodeStatus.RUNNING.value: "🔄",
                NodeStatus.COMPLETED.value: "✅",
                NodeStatus.FAILED.value: "❌"
            }.get(status, "❓")
            print(f"    {emoji} {status}: {count}")
        
        print("\n🔗 节点详情:")
        for node_id, node in self.nodes.items():
            parents = self.get_parent_nodes(node_id)
            children = self.adjacency_list.get(node_id, [])
            
            status_emoji = {
                NodeStatus.PENDING.value: "⏳",
                NodeStatus.RUNNING.value: "🔄",
                NodeStatus.COMPLETED.value: "✅",
                NodeStatus.FAILED.value: "❌"
            }.get(node.status.value, "❓")
            
            print(f"  {status_emoji} {node.name} ({node.node_type.value}):")
            print(f"    状态: {node.status.value}")
            print(f"    内容: {node.content[:50]}{'...' if len(node.content) > 50 else ''}")
            
            if parents:
                parent_names = [self.nodes[pid].name for pid in parents]
                print(f"    依赖: {', '.join(parent_names)}")
            
            if children:
                child_names = [self.nodes[cid].name for cid in children]
                print(f"    后续: {', '.join(child_names)}")
            
            if node.error:
                print(f"    错误: {node.error}")
            
            print()
    
    def export_dot(self, filename: str = "graph.dot") -> None:
        """导出为DOT格式文件，可用于Graphviz渲染
        
        Args:
            filename: 输出文件名
        """
        dot_content = ["digraph SearchGraph {"]
        dot_content.append("  rankdir=TB;")
        dot_content.append("  node [shape=box, style=filled];")
        
        # 定义节点样式
        node_styles = {
            NodeType.ROOT.value: 'fillcolor="#FF6B6B", fontcolor="white"',
            NodeType.SEARCH.value: 'fillcolor="#4ECDC4", fontcolor="white"',
            NodeType.RESULT.value: 'fillcolor="#45B7D1", fontcolor="white"',
            NodeType.END.value: 'fillcolor="#96CEB4", fontcolor="white"'
        }
        
        # 添加节点
        for node_id, node in self.nodes.items():
            style = node_styles.get(node.node_type.value, 'fillcolor="#CCCCCC"')
            label = f"{node.name}\\n({node.status.value})"
            dot_content.append(f'  "{node_id}" [label="{label}", {style}];')
        
        # 添加边
        for edge in self.edges.values():
            dot_content.append(f'  "{edge.from_node}" -> "{edge.to_node}";')
        
        dot_content.append("}")
        
        # 写入文件
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(dot_content))
        
        print(f"✅ DOT文件已导出到: {filename}")
        print(f"💡 使用Graphviz渲染: dot -Tpng {filename} -o graph.png")