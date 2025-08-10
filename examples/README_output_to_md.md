# Graph Search Example 输出保存功能使用说明

## 📋 功能概述

我们已经成功修改了 `examples/graph_search_example.py` 文件，现在所有的控制台输出都会被自动保存到 markdown 文件中，方便您查看完整的执行过程和结果。

## 🔧 主要改进

### 1. 输出记录系统
- **新增 `log_output()` 函数**: 替代所有的 `print()` 语句
- **输出缓冲区**: 使用 `output_buffer` 列表收集所有输出
- **双重输出**: 既显示在控制台，又保存到缓冲区

### 2. Markdown 文件生成
- **自动保存**: 执行完成后自动生成 markdown 文件
- **时间戳命名**: 文件名包含执行时间，避免覆盖
- **格式化输出**: 保持原有的格式和emoji表情

### 3. 完整的执行记录
- **搜索进度**: 记录每个搜索步骤的进度
- **节点状态**: 详细记录每个节点的执行状态
- **错误信息**: 保存所有错误和异常信息
- **统计数据**: 完整的执行统计和性能分析

## 🚀 使用方法

### 基本使用

```bash
# 进入项目目录
cd /Users/weifuqiang/Desktop/llmsearch/MindSearch-myself/langchain_rebuild

# 运行示例脚本
python examples/graph_search_example.py
```

### 输出文件

执行完成后，会在当前目录生成一个markdown文件：
```
graph_search_example_output_YYYYMMDD_HHMMSS.md
```

例如：`graph_search_example_output_20250808_150601.md`

## 📄 输出文件内容

生成的markdown文件包含以下内容：

### 1. 文件头部
```markdown
# MindSearchAgent 图状态管理功能演示输出

**执行时间**: 2025-08-08 15:06:01

---
```

### 2. 执行过程
- 🚀 功能演示开始
- 📖 使用指南
- 🔍 查询执行过程
- 📢 搜索进度更新
- 📊 图执行统计
- 🎯 搜索结果
- ✅/❌ 节点执行状态
- 🎉 执行完成

### 3. 详细信息
- **节点统计**: 总数、成功数、失败数、成功率
- **执行时间**: 详细的时间统计
- **错误信息**: 完整的错误堆栈和处理过程
- **图结构**: 节点类型分布和连接关系

## 🧪 测试验证

我们提供了测试脚本来验证功能：

```bash
# 运行测试脚本
python test_output_to_md.py
```

测试脚本会：
1. ✅ 模拟完整的执行过程
2. ✅ 生成测试输出文件
3. ✅ 验证文件内容完整性
4. ✅ 检查格式和编码

## 📊 示例输出

以下是一个典型的输出文件片段：

```markdown
📢 搜索进度更新
   step: 1
   total: 5
   status: running

📊 图执行统计:
  总节点数: 5
  已完成节点: 3
  失败节点: 2
  成功率: 60.00%
  执行时间: 15.50秒

  节点详情:
    ✅ search_0: completed
    ✅ search_1: completed
    ❌ search_2: failed
      错误: SSL connection error
    ✅ search_3: completed
    ❌ search_4: failed
      错误: Timeout
```

## 💡 使用建议

### 1. 长时间执行
对于复杂查询，建议使用输出保存功能：
- 避免控制台输出被覆盖
- 便于后续分析和调试
- 可以保存多次执行的历史记录

### 2. 调试和分析
- 查看完整的执行流程
- 分析节点失败原因
- 优化查询策略
- 性能分析和改进

### 3. 文档和报告
- 生成执行报告
- 分享执行结果
- 问题排查记录
- 性能基准测试

## 🔧 自定义配置

### 修改输出格式

如果需要自定义输出格式，可以修改 `save_output_to_markdown()` 函数：

```python
def save_output_to_markdown():
    """将输出保存到markdown文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"custom_output_{timestamp}.md"  # 自定义文件名
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# 自定义标题\n\n")  # 自定义标题
        # ... 其他自定义内容
```

### 修改文件位置

如果需要将文件保存到特定目录：

```python
output_dir = "outputs"  # 指定输出目录
os.makedirs(output_dir, exist_ok=True)
filename = os.path.join(output_dir, f"output_{timestamp}.md")
```

## 🎯 总结

通过这次改进，`graph_search_example.py` 现在具备了：

✅ **完整记录**: 所有执行过程都被保存
✅ **格式友好**: markdown格式便于阅读和分享
✅ **时间戳**: 避免文件覆盖，保留历史记录
✅ **双重输出**: 既有实时显示，又有文件保存
✅ **错误处理**: 完整记录错误和异常信息
✅ **统计分析**: 详细的性能和执行统计

现在您可以放心运行复杂的查询，所有的执行过程和结果都会被完整保存，便于后续查看和分析！