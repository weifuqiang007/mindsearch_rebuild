# MindSearchAgent 图状态管理功能指南

## 概述

本项目为 MindSearchAgent 添加了图状态管理功能，使其能够更智能地处理复杂查询。图状态管理提供了查询执行的可视化、并行处理、依赖管理和详细统计等功能。

## 核心组件

### 1. SimpleSearchGraph (core/simple_graph.py)

图状态管理的核心类，提供以下功能：

- **节点管理**: 创建和管理不同类型的节点（ROOT、SEARCH、RESULT、END）
- **边管理**: 建立节点之间的依赖关系
- **状态跟踪**: 跟踪每个节点的执行状态（PENDING、RUNNING、COMPLETED、FAILED）
- **执行调度**: 获取可以执行的节点（所有依赖都已完成）

```python
from core.simple_graph import SimpleSearchGraph, NodeType, NodeStatus

# 创建图
graph = SimpleSearchGraph()

# 添加节点
root_id = graph.add_node("root", "根节点", NodeType.ROOT)
search_id = graph.add_node("search", "搜索节点", NodeType.SEARCH)

# 添加边（依赖关系）
graph.add_edge(root_id, search_id)

# 更新节点状态
graph.update_node_status(root_id, NodeStatus.COMPLETED)

# 获取可执行节点
ready_nodes = graph.get_ready_nodes()
```

### 2. 增强的 MindSearchAgent (agents/mindsearch_agent.py)

原有的 MindSearchAgent 现在集成了图状态管理功能：

#### 新增方法：

- `_create_search_graph(query_plan)`: 根据查询计划创建搜索图
- `_execute_graph_search(graph, callback)`: 执行基于图的搜索
- `_execute_graph_sub_query(graph, node_id, sub_query, callback)`: 执行单个图节点的子查询
- `get_graph_statistics()`: 获取图执行统计信息

#### 工作流程：

1. **查询分析**: 分析用户查询并生成查询计划
2. **图创建**: 根据查询计划创建搜索图
3. **图执行**: 按照依赖关系并行执行搜索节点
4. **结果生成**: 汇总所有搜索结果并生成最终答案

## 使用示例

### 基本使用

```python
import asyncio
from agents.mindsearch_agent import MindSearchAgent
from core.search_manager import SearchManager

async def example():
    # 创建搜索管理器
    search_manager = SearchManager()
    
    # 创建 MindSearchAgent
    agent = MindSearchAgent(
        search_manager=search_manager,
        max_sub_queries=5,
        max_search_results=10
    )
    
    # 定义回调函数监控进度
    def callback(message: str, **kwargs):
        print(f"进度: {message}")
    
    # 执行搜索
    result = await agent.asearch(
        query="人工智能的发展历史和应用领域",
        callback=callback
    )
    
    print(f"搜索结果: {result}")
    
    # 获取统计信息
    stats = agent.get_session_statistics()
    print(f"图统计: {stats.get('graph_stats', {})}")

# 运行示例
asyncio.run(example())
```

### 高级使用

查看 `examples/graph_search_example.py` 获取更详细的使用示例，包括：

- 复杂查询处理
- 图可视化
- 错误处理
- 性能统计

## 图功能优势

### 1. 并行执行

独立的子查询可以并行执行，提高整体查询效率：

```
原始查询: "AI的历史、应用和未来"

图结构:
root → search_history (AI历史)
    → search_applications (AI应用) 
    → search_future (AI未来)
    → result → end

执行顺序:
步骤1: 执行 search_history
步骤2: 并行执行 search_applications 和 search_future
步骤3: 执行 result 汇总
步骤4: 执行 end 结束
```

### 2. 智能依赖管理

自动处理子查询之间的依赖关系：

```python
# 子查询依赖示例
sub_queries = [
    SubQuery(id="q1", query="基础概念", dependencies=[]),
    SubQuery(id="q2", query="高级应用", dependencies=["q1"]),  # 依赖 q1
    SubQuery(id="q3", query="实际案例", dependencies=["q1", "q2"])  # 依赖 q1 和 q2
]

# 图会自动按依赖顺序执行：q1 → q2 → q3
```

### 3. 错误处理和恢复

智能处理节点失败和依赖错误：

- 单个节点失败不会影响其他独立节点
- 依赖失败的节点会被自动标记为失败
- 提供详细的错误信息和统计

### 4. 详细统计信息

提供丰富的执行统计信息：

```python
stats = agent.get_session_statistics()
graph_stats = stats['graph_stats']

print(f"总节点数: {graph_stats['total_nodes']}")
print(f"成功率: {graph_stats['success_rate']:.2%}")
print(f"执行时间: {graph_stats['execution_time']:.2f}秒")
```

## 测试

### 运行图功能测试

```bash
# 测试图结构和执行逻辑（不依赖搜索引擎）
python test/test_graph_only.py

# 测试完整的图搜索功能
python test/test_graph_search.py

# 运行使用示例
python examples/graph_search_example.py
```

### 测试输出示例

```
=== 测试图创建和执行流程 ===

📊 图统计:
  节点数: 6
  边数: 7

🔄 模拟执行流程:
  步骤 1: 执行 1 个节点
    执行节点: search_q1 (search)
      ✅ 成功
  步骤 2: 执行 2 个节点
    执行节点: search_q2 (search)
      ✅ 成功
    执行节点: search_q3 (search)
      ✅ 成功
  步骤 3: 执行 1 个节点
    执行节点: result (result)
      ✅ 完成
  步骤 4: 执行 1 个节点
    执行节点: end (end)
      ✅ 完成
  步骤 5: 所有节点执行完成

📈 最终状态统计:
  completed: 6 个节点
  成功率: 100.00%
```

## 配置选项

### MindSearchAgent 参数

- `max_sub_queries`: 最大子查询数量（默认: 5）
- `max_search_results`: 每个子查询的最大搜索结果数（默认: 10）
- `search_manager`: 搜索管理器实例

### 回调函数

回调函数用于监控搜索进度，接收以下参数：

- `message`: 进度消息
- `**kwargs`: 额外信息（如图对象、节点信息等）

```python
def callback(message: str, **kwargs):
    print(f"📢 {message}")
    
    # 处理图相关信息
    if 'graph' in kwargs:
        graph = kwargs['graph']
        ready_nodes = graph.get_ready_nodes()
        print(f"可执行节点: {len(ready_nodes)}")
    
    # 处理其他信息
    for key, value in kwargs.items():
        if key != 'graph':
            print(f"  {key}: {value}")
```

## 性能优化建议

1. **合理设置参数**: 根据查询复杂度调整 `max_sub_queries` 和 `max_search_results`
2. **使用回调监控**: 通过回调函数监控长时间运行的查询
3. **错误处理**: 实现适当的错误处理逻辑
4. **统计分析**: 定期分析统计信息以优化查询策略

## 故障排除

### 常见问题

1. **导入错误**: 确保在正确的项目目录中运行脚本
2. **搜索引擎配置**: 确保搜索管理器正确配置
3. **依赖循环**: 检查子查询依赖关系是否存在循环
4. **内存使用**: 对于大型查询，注意内存使用情况

### 调试技巧

1. 使用详细的回调函数监控执行过程
2. 检查图统计信息了解执行状态
3. 查看节点详情了解失败原因
4. 使用测试脚本验证图功能

## 未来扩展

图状态管理功能为未来扩展提供了良好的基础：

1. **可视化界面**: 实时显示图执行状态
2. **动态调整**: 根据执行情况动态调整图结构
3. **缓存机制**: 缓存子查询结果以提高效率
4. **分布式执行**: 支持跨多个节点的分布式查询执行
5. **智能调度**: 基于资源使用情况的智能节点调度

## 总结

图状态管理功能显著增强了 MindSearchAgent 的能力，提供了：

- ✅ 更高的查询执行效率
- ✅ 更好的错误处理和恢复
- ✅ 详细的执行统计和监控
- ✅ 可扩展的架构设计
- ✅ 易于使用的API接口

通过这些功能，MindSearchAgent 现在能够更智能、更高效地处理复杂的搜索查询任务。