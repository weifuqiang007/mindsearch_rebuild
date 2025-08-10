# MindSearchAgent 图可视化功能使用指南

## 概述

MindSearchAgent 现在支持图可视化功能，可以直观地展示搜索图的结构、节点状态和执行流程。这个功能帮助用户更好地理解复杂查询的分解过程和执行状态。

## 功能特性

### 1. 图形化可视化
- 使用 matplotlib 和 networkx 生成高质量的图形
- 支持不同的节点类型和状态颜色编码
- 可自定义图片大小、标题和保存路径
- 自动布局优化，确保图形清晰易读

### 2. 文本结构打印
- 快速查看图的基本信息（节点数、边数）
- 详细的节点状态和类型信息
- 适合在终端或日志中查看

### 3. DOT 格式导出
- 导出为 Graphviz DOT 格式
- 支持使用专业图形工具进一步编辑
- 便于集成到文档或报告中

## 安装依赖

在使用图可视化功能之前，请确保安装必要的依赖：

```bash
pip install matplotlib networkx
```

## 使用方法

### 1. 基本使用

```python
from agents.mindsearch_agent import MindSearchAgent
from core.search_manager import SearchManager

# 创建搜索代理
search_manager = SearchManager()
agent = MindSearchAgent(
    search_manager=search_manager,
    enable_graph_search=True  # 启用图搜索功能
)

# 执行搜索（这会创建搜索图）
result = agent.search("人工智能在医疗领域的应用")

# 可视化搜索图
agent.visualize_search_graph()
```

### 2. 自定义可视化选项

```python
# 保存图片到指定路径
agent.visualize_search_graph(
    save_path="my_search_graph.png",
    title="AI医疗应用搜索图",
    figsize=(16, 12),
    show_labels=True
)
```

### 3. 打印文本结构

```python
# 在终端中查看图结构
agent.print_search_graph()
```

### 4. 导出 DOT 格式

```python
# 导出为 DOT 格式
agent.export_graph_dot("search_graph.dot")

# 使用 Graphviz 渲染（需要安装 Graphviz）
# dot -Tpng search_graph.dot -o graph.png
```

## API 参考

### `visualize_search_graph()`

可视化当前搜索图。

**参数：**
- `save_path` (Optional[str]): 保存图片的路径，如果为 None 则显示图片
- `show_labels` (bool): 是否显示节点标签，默认为 True
- `figsize` (tuple): 图片大小，默认为 (12, 8)
- `title` (str): 图片标题，默认为 "MindSearch 搜索图"

### `print_search_graph()`

打印当前搜索图的文本结构。

### `export_graph_dot()`

导出搜索图为 DOT 格式。

**参数：**
- `filename` (str): 输出文件名，默认为 "search_graph.dot"

## 节点类型和状态

### 节点类型
- **ROOT**: 根节点（蓝色）
- **SEARCH**: 搜索节点（绿色）
- **RESULT**: 结果节点（橙色）
- **END**: 结束节点（紫色）

### 节点状态
- **PENDING**: 等待执行（浅灰色）
- **RUNNING**: 执行中（黄色）
- **COMPLETED**: 已完成（深绿色）
- **FAILED**: 执行失败（红色）

## 示例输出

### 文本结构示例
```
📊 搜索图结构概览:
   节点数: 6
   边数: 5
   
📋 节点详情:
   [ROOT] root (COMPLETED): 原始查询: 人工智能在医疗领域的应用
   [SEARCH] search_sq_1 (COMPLETED): 人工智能的定义
   [SEARCH] search_sq_2 (COMPLETED): 机器学习算法分类
   [SEARCH] search_sq_3 (FAILED): 深度学习应用案例
   [RESULT] result (PENDING): 汇总所有搜索结果
   [END] end (PENDING): 搜索完成
```

## 故障排除

### 1. 中文字体问题
如果在图片中看到中文字符显示为方框，可以安装中文字体：

```python
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
```

### 2. 图片不显示
如果在某些环境中图片无法显示，请使用 `save_path` 参数保存图片：

```python
agent.visualize_search_graph(save_path="graph.png")
```

### 3. 依赖缺失
如果遇到导入错误，请确保安装了所有必要的依赖：

```bash
pip install matplotlib networkx
```

## 高级用法

### 1. 批量可视化

```python
queries = [
    "机器学习的基本概念",
    "深度学习在计算机视觉中的应用",
    "自然语言处理的发展趋势"
]

for i, query in enumerate(queries):
    agent = MindSearchAgent(search_manager, enable_graph_search=True)
    result = agent.search(query)
    agent.visualize_search_graph(
        save_path=f"graph_{i+1}.png",
        title=f"查询{i+1}: {query[:20]}..."
    )
```

### 2. 实时监控

```python
def progress_callback(callback_type: str, data: dict):
    if callback_type == "node_completed":
        print(f"✅ 节点完成: {data.get('node_name')}")
        # 实时更新可视化
        agent.visualize_search_graph(save_path="current_progress.png")

agent.callback_func = progress_callback
result = agent.search("复杂查询")
```

## 总结

图可视化功能为 MindSearchAgent 提供了强大的调试和监控能力，帮助用户：

1. **理解查询分解**: 直观查看复杂查询如何被分解为子问题
2. **监控执行进度**: 实时了解各个节点的执行状态
3. **调试问题**: 快速定位失败的节点和错误原因
4. **优化性能**: 分析执行流程，识别瓶颈和优化机会
5. **文档记录**: 生成图形化的执行报告

通过这些功能，用户可以更好地理解和优化 MindSearchAgent 的搜索过程。