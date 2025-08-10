# Python 相对导入问题解决方案

## 问题描述

当直接运行 `test.py` 时出现错误：
```
ImportError: attempted relative import beyond top-level package
```

## 问题原因

### 技术原理

1. **主模块问题**：当直接运行 `python test.py` 时，Python 将 `test.py` 视为主模块（`__name__ == '__main__'`），而不是包的一部分

2. **相对导入限制**：相对导入（如 `from ..config import get_settings`）只能在包内部使用，需要当前模块是包的一部分

3. **导入链问题**：
   ```
   test.py → core.search_tools → ..config (相对导入失败)
   test.py → core.__init__.py → llm_manager → ..config (相对导入失败)
   ```

### 具体错误流程

1. `test.py` 导入 `core.search_tools`
2. `core/__init__.py` 被执行，导入 `llm_manager`
3. `llm_manager.py` 尝试执行 `from ..config import get_settings`
4. 由于 `test.py` 是主模块，`__package__` 为 `None`，相对导入失败

## 解决方案

### 方案1：修改导入方式（推荐）✅

在使用相对导入的模块中添加兼容性导入：

```python
# 修改前
from ..config import get_settings

# 修改后
try:
    from ..config import get_settings
except ImportError:
    from langchain_rebuild.config import get_settings
```

**优势**：
- 兼容两种运行方式
- 不影响现有代码结构
- 向后兼容

**已修改的文件**：
- `core/llm_manager.py`
- `core/search_tools.py`

### 方案2：使用模块方式运行

```bash
# 从项目根目录运行
cd /Users/weifuqiang/Desktop/llmsearch/MindSearch-myself
python -m langchain_rebuild.test
```

### 方案3：设置 PYTHONPATH

```bash
# 设置环境变量
export PYTHONPATH=/Users/weifuqiang/Desktop/llmsearch/MindSearch-myself:$PYTHONPATH

# 或者临时设置
PYTHONPATH=/Users/weifuqiang/Desktop/llmsearch/MindSearch-myself:$PYTHONPATH python langchain_rebuild/test.py
```

### 方案4：创建独立测试文件

创建不依赖相对导入的测试文件（如 `test_standalone.py`）

## 最佳实践

### 1. 导入规范

```python
# ✅ 推荐：兼容性导入
try:
    from ..config import get_settings  # 包内使用
except ImportError:
    from langchain_rebuild.config import get_settings  # 直接运行时

# ✅ 推荐：绝对导入（如果可能）
from langchain_rebuild.config import get_settings

# ❌ 避免：纯相对导入（在可能直接运行的模块中）
from ..config import get_settings
```

### 2. 项目结构建议

```
project/
├── langchain_rebuild/          # 主包
│   ├── __init__.py
│   ├── config.py
│   ├── core/                   # 子包
│   │   ├── __init__.py
│   │   ├── llm_manager.py     # 使用兼容性导入
│   │   └── search_tools.py    # 使用兼容性导入
│   └── test.py                # 测试文件
└── tests/                     # 独立测试目录
    └── test_standalone.py     # 不依赖相对导入
```

### 3. 运行方式

```bash
# 方式1：模块运行（推荐）
python -m langchain_rebuild.test

# 方式2：设置路径后直接运行
PYTHONPATH=/path/to/project:$PYTHONPATH python langchain_rebuild/test.py

# 方式3：从正确目录运行（需要修改导入）
cd /path/to/project && python langchain_rebuild/test.py
```

## 验证解决方案

### 测试命令

```bash
# 测试1：直接运行（需要设置PYTHONPATH）
cd /Users/weifuqiang/Desktop/llmsearch/MindSearch-myself
PYTHONPATH=/Users/weifuqiang/Desktop/llmsearch/MindSearch-myself:$PYTHONPATH python langchain_rebuild/test.py

# 测试2：模块运行
cd /Users/weifuqiang/Desktop/llmsearch/MindSearch-myself
python -m langchain_rebuild.test

# 测试3：独立测试文件
cd /Users/weifuqiang/Desktop/llmsearch/MindSearch-myself/langchain_rebuild
python test_standalone.py
```

### 预期结果

```
✅ 成功导入搜索工具
```

## 总结

这个问题是 Python 包系统中常见的相对导入问题。通过添加兼容性导入，我们可以让代码在两种情况下都正常工作：

1. **包内使用**：相对导入正常工作
2. **直接运行**：回退到绝对导入

这种解决方案保持了代码的灵活性和兼容性，是处理此类问题的最佳实践。