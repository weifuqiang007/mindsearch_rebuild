# LangChain MindSearch

基于 LangChain 重构的智能搜索系统，实现了与原版 MindSearch 相同的功能，但使用更现代化的架构和更稳定的技术栈。

## 🌟 特性

- **多智能体架构**: 支持 MindSearch、ReAct、搜索等多种智能体
- **多LLM支持**: 支持 OpenAI、Anthropic、SiliconFlow 等多种LLM提供商
- **多搜索引擎**: 集成 Bing、Google、DuckDuckGo、Serper 等搜索引擎
- **流式响应**: 支持实时流式输出，提升用户体验
- **RESTful API**: 完整的 REST API 接口
- **WebSocket支持**: 实时双向通信
- **引用管理**: 自动生成和管理搜索结果引用
- **可扩展架构**: 模块化设计，易于扩展和维护

## 🏗️ 系统架构

```
langchain_rebuild/
├── config.py              # 统一配置管理
├── core/                  # 核心组件
│   ├── llm_manager.py     # LLM管理器
│   ├── search_tools.py    # 搜索工具管理
│   ├── query_decomposer.py # 查询分解器
│   └── reference_manager.py # 引用管理器
├── agents/                # 智能体模块
│   ├── mindsearch_agent.py # MindSearch智能体
│   ├── react_agent.py     # ReAct智能体
│   └── search_agent.py    # 搜索智能体
├── api/                   # API层
│   ├── server.py          # FastAPI服务器
│   ├── routes.py          # 路由定义
│   ├── middleware.py      # 中间件
│   └── websocket.py       # WebSocket支持
├── main.py               # 主启动文件
├── run.py                # 简单启动脚本
└── test_basic.py         # 基础功能测试
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd langchain_rebuild
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# LLM配置
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
SILICONFLOW_API_KEY=your_siliconflow_api_key

# 搜索引擎配置
BING_SEARCH_API_KEY=your_bing_api_key
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_google_engine_id
SERPER_API_KEY=your_serper_api_key

# 服务器配置
SERVER_HOST=localhost
SERVER_PORT=8000
```

### 3. 运行测试

```bash
python test_basic.py
```

### 4. 启动服务器

```bash
# 使用简单启动脚本
python run.py

# 或使用主启动文件
python main.py --reload
```

### 5. 访问服务

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **WebSocket**: ws://localhost:8000/ws/{session_id}

## 📚 API 使用示例

### 搜索API

```bash
# 基础搜索
curl -X POST "http://localhost:8000/api/v1/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什么是人工智能？",
    "max_results": 10,
    "strategy": "single_engine"
  }'

# 流式搜索
curl -X POST "http://localhost:8000/api/v1/search/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "机器学习的应用",
    "strategy": "multi_engine"
  }'
```

### 对话API

```bash
# 基础对话
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "请介绍一下深度学习",
    "session_id": "test_session"
  }'

# 流式对话
curl -X POST "http://localhost:8000/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "解释神经网络的工作原理",
    "session_id": "test_session",
    "stream": true
  }'
```

### ReAct API

```bash
# ReAct问题解决
curl -X POST "http://localhost:8000/api/v1/react/" \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "如何提高机器学习模型的准确率？",
    "max_steps": 10
  }'
```

## 🔌 WebSocket 使用

```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/my_session');

// 发送搜索请求
ws.send(JSON.stringify({
  type: 'search',
  data: {
    query: '人工智能的发展历史',
    strategy: 'multi_engine',
    max_results: 10
  }
}));

// 接收响应
ws.onmessage = function(event) {
  const response = JSON.parse(event.data);
  console.log('收到响应:', response);
};
```

## 🔧 配置说明

### LLM配置

```python
class LLMConfig(BaseSettings):
    default_provider: str = "openai"  # 默认LLM提供商
    max_tokens: int = 4000           # 最大token数
    temperature: float = 0.7         # 温度参数
    timeout: int = 30               # 超时时间
```

### 搜索配置

```python
class SearchConfig(BaseSettings):
    default_engine: str = "bing"     # 默认搜索引擎
    max_results: int = 10           # 最大结果数
    timeout: int = 10               # 超时时间
    enable_cache: bool = True       # 启用缓存
```

### 服务器配置

```python
class ServerConfig(BaseSettings):
    host: str = "localhost"         # 服务器主机
    port: int = 8000               # 服务器端口
    cors_origins: List[str] = ["*"] # CORS设置
    max_request_size: int = 10485760 # 最大请求大小
```

## 🧪 测试

### 运行基础测试

```bash
python test_basic.py
```

### 测试覆盖的模块

- ✅ 配置模块
- ✅ 核心模块 (LLM管理器、搜索工具、查询分解器、引用管理器)
- ✅ 智能体模块 (MindSearch、ReAct、搜索智能体)
- ✅ API组件 (FastAPI应用创建)
- ✅ 简单功能 (查询分解、关键词提取)

## 🔍 核心组件说明

### 1. LLM管理器

统一管理多种LLM提供商，提供标准化接口：

- 支持 OpenAI、Anthropic、SiliconFlow
- 同步/异步调用
- 流式响应
- 自动重试和错误处理

### 2. 搜索工具管理器

集成多种搜索引擎，提供统一搜索接口：

- 支持 Bing、Google、DuckDuckGo、Serper
- 多引擎并发搜索
- 结果聚合和去重
- 搜索结果缓存

### 3. 查询分解器

智能分解复杂查询：

- 查询类型识别
- 子查询分解
- 关键词提取
- 查询计划构建

### 4. 引用管理器

管理搜索结果引用：

- 自动生成引用
- 多种引用格式
- 可信度评估
- 来源验证

### 5. 智能体系统

#### MindSearch智能体
- 复杂查询处理
- 多轮对话支持
- 搜索结果分析
- 综合答案生成

#### ReAct智能体
- 推理-行动循环
- 步骤化问题解决
- 思考过程可视化
- 多种行动类型

#### 搜索智能体
- 专业搜索处理
- 多种搜索策略
- 结果质量评估
- 搜索优化

## 🚀 部署

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run.py"]
```

### 生产环境

```bash
# 使用gunicorn部署
gunicorn langchain_rebuild.api.server:create_app \
  --factory \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker
```

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 感谢 [InternLM MindSearch](https://github.com/InternLM/MindSearch) 项目提供的灵感和架构设计
- 感谢 LangChain 社区提供的优秀框架
- 感谢所有贡献者的支持

## 📞 联系

如有问题或建议，请通过以下方式联系：

- 创建 Issue
- 发送邮件
- 加入讨论群

---

**注意**: 这是一个基于 LangChain 的重构版本，旨在提供更稳定和可扩展的智能搜索解决方案。