# MindSearch 配置指南

本指南将帮助您正确配置 MindSearch 系统的各个组件。

## 📋 配置文件说明

系统使用 `.env` 文件进行配置。请复制 `.env.example` 文件并重命名为 `.env`，然后根据您的需求修改配置。

## 🤖 LLM 配置

### 硅基流动 (推荐)

```bash
# 硅基流动配置
SILICONFLOW_API_KEY=your_siliconflow_api_key
SILICONFLOW_MODEL=Qwen/QwQ-32B
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1

# 设置为默认提供商
DEFAULT_LLM_PROVIDER=siliconflow
```

### OpenAI

```bash
# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4-turbo-preview

# 设置为默认提供商
DEFAULT_LLM_PROVIDER=openai
```

### Anthropic

```bash
# Anthropic 配置
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# 设置为默认提供商
DEFAULT_LLM_PROVIDER=anthropic
```

## 🐘 PostgreSQL 数据库配置

```bash
# PostgreSQL 配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mindsearch
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# 连接池配置 (可选)
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20
POSTGRES_POOL_TIMEOUT=30
POSTGRES_POOL_RECYCLE=3600
```

### 数据库连接示例

```python
from sqlalchemy import create_engine
from langchain_rebuild.config import get_postgres_config

postgres_config = get_postgres_config()
engine = create_engine(postgres_config.database_url)
```

## 🔴 Redis 配置

```bash
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password  # 可选

# 连接池配置
REDIS_MAX_CONNECTIONS=20

# 缓存配置
CACHE_TTL=3600
SESSION_TTL=86400
```

### Redis 连接示例

```python
import redis
from langchain_rebuild.config import get_redis_config

redis_config = get_redis_config()

# 方式1: 使用URL
redis_client = redis.from_url(redis_config.redis_url)

# 方式2: 使用参数
redis_client = redis.Redis(
    host=redis_config.host,
    port=redis_config.port,
    db=redis_config.db,
    password=redis_config.password,
    max_connections=redis_config.max_connections
)
```

## 🌐 服务器配置

```bash
# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=true

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/path/to/logfile.log  # 可选

# CORS 配置
CORS_ORIGINS=["*"]
CORS_METHODS=["*"]
CORS_HEADERS=["*"]
```

## 🔍 搜索引擎配置

```bash
# 搜索引擎配置
DEFAULT_SEARCH_ENGINE=duckduckgo

# 搜索参数
MAX_SEARCH_RESULTS=10
SEARCH_TIMEOUT=30
MAX_CONTENT_LENGTH=5000
ENABLE_CONTENT_EXTRACTION=true
```

## 🤖 智能体配置

```bash
# 智能体配置
MAX_SUB_QUESTIONS=5
MAX_ITERATIONS=10
MAX_SEARCH_DEPTH=3
MAX_GRAPH_NODES=20

# 响应配置
MAX_RESPONSE_LENGTH=2000
INCLUDE_REFERENCES=true
ENABLE_STREAMING=true
STREAM_CHUNK_SIZE=50

# 超时配置
AGENT_TIMEOUT=300
SEARCH_TIMEOUT=60
```

## 📝 配置使用示例

### 获取配置

```python
from langchain_rebuild.config import (
    get_settings,
    get_llm_config,
    get_postgres_config,
    get_redis_config,
    get_server_config,
    get_agent_config
)

# 获取所有配置
settings = get_settings()

# 获取特定配置
llm_config = get_llm_config()
db_config = get_postgres_config()
redis_config = get_redis_config()
```

### 使用 LLM

```python
from langchain_openai import ChatOpenAI
from langchain_rebuild.config import get_llm_config

llm_config = get_llm_config()

if llm_config.default_provider == "siliconflow":
    llm = ChatOpenAI(
        api_key=llm_config.siliconflow_api_key,
        base_url=llm_config.siliconflow_base_url,
        model=llm_config.siliconflow_model,
        temperature=llm_config.temperature
    )
elif llm_config.default_provider == "openai":
    llm = ChatOpenAI(
        api_key=llm_config.openai_api_key,
        model=llm_config.openai_model,
        temperature=llm_config.temperature
    )

# 使用 LLM
response = llm.invoke("你好，请介绍一下你自己")
print(response.content)
```

## 🔧 配置验证

运行配置示例来验证您的配置是否正确：

```bash
cd langchain_rebuild
python config_example.py
```

这将显示所有配置信息和使用示例。

## ⚠️ 注意事项

1. **API 密钥安全**: 请确保不要将 API 密钥提交到版本控制系统中
2. **数据库连接**: 确保 PostgreSQL 和 Redis 服务正在运行
3. **端口冲突**: 确保配置的端口没有被其他服务占用
4. **环境变量**: 系统使用 Pydantic 的 `alias` 功能读取环境变量，确保变量名完全匹配

## 🚀 快速开始

1. 复制配置文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入您的配置信息

3. 验证配置：
   ```bash
   python config_example.py
   ```

4. 启动服务：
   ```bash
   python run.py
   ```

现在您可以访问 `http://localhost:8000` 来使用 MindSearch 系统了！