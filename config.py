"""配置管理模块

统一管理系统配置，支持环境变量和配置文件
"""
import os
from typing import Optional, List
from pydantic import Field
# 使用 pydantic_settings 进行配置管理的优势:
# 1. 类型检查和验证 - 自动验证配置值的类型和格式
# 2. 环境变量集成 - 无缝支持从环境变量加载配置
# 3. 配置继承和嵌套 - 支持复杂的配置层次结构
# 4. IDE 智能提示 - 类型注解提供更好的开发体验
# 5. 配置文档化 - 通过类定义清晰地展示配置结构
# 6. 默认值管理 - 统一且优雅地处理默认配置
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv, dotenv_values

# need_load_env = ".env"
need_load_dev_env = ".dev_env"


class LLMConfig(BaseSettings):
    """LLM 配置"""
    
    model_config = SettingsConfigDict(
        env_file=".dev_env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # OpenAI 配置
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, env="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    
    # Anthropic 配置
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
    
    # SiliconFlow 配置
    siliconflow_api_key: Optional[str] = Field(default=None, env="SILICONFLOW_API_KEY")
    siliconflow_base_url: str = Field(default="https://api.siliconflow.cn/v1", env="SILICONFLOW_BASE_URL")
    siliconflow_model: str = Field(default="Qwen/QwQ-32B", env="SILICONFLOW_MODEL")
    
    # 默认 LLM 提供商
    default_provider: str = Field(default="openai", alias="DEFAULT_LLM_PROVIDER")
    
    # 通用配置
    temperature: float = Field(default=0.1, env="LLM_TEMPERATURE")
    max_tokens: int = Field(default=4000, env="LLM_MAX_TOKENS")
    timeout: int = Field(default=60, env="LLM_TIMEOUT")


class SearchConfig(BaseSettings):
    """搜索引擎配置"""
    
    model_config = SettingsConfigDict(
        env_file=need_load_dev_env,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Bing Search
    bing_api_key: Optional[str] = Field(default=None, env="BING_SEARCH_API_KEY")
    bing_endpoint: str = Field(default="https://api.bing.microsoft.com/v7.0/search", env="BING_ENDPOINT")
    
    # Google Search
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    google_cse_id: Optional[str] = Field(default=None, env="GOOGLE_CSE_ID")
    
    # Serper API
    serper_api_key: Optional[str] = Field(default=None, env="SERPER_API_KEY")
    
    # DuckDuckGo (无需 API Key)
    
    # 搜索配置
    default_engine: str = Field(default="google", env="DEFAULT_SEARCH_ENGINE")
    default_search_engine: str = Field(default="google", env="DEFAULT_SEARCH_ENGINE")
    max_search_results: int = Field(default=10, env="MAX_SEARCH_RESULTS")
    search_timeout: int = Field(default=30, env="SEARCH_TIMEOUT")
    
    # 内容抓取
    max_content_length: int = Field(default=5000, env="MAX_CONTENT_LENGTH")
    enable_content_extraction: bool = Field(default=True, env="ENABLE_CONTENT_EXTRACTION")


class ServerConfig(BaseSettings):
    """服务器配置"""
    
    model_config = SettingsConfigDict(
        env_file=need_load_dev_env,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8002, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # CORS 配置
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_methods: List[str] = Field(default=["*"], env="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")


class PostgreSQLConfig(BaseSettings):
    """PostgreSQL 数据库配置"""
    
    model_config = SettingsConfigDict(
        env_file=need_load_dev_env,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    port: int = Field(default=5432, alias="POSTGRES_PORT")
    db: str = Field(default="mindsearch", env="POSTGRES_DB")
    user: str = Field(default="postgres", env="POSTGRES_USER")
    password: Optional[str] = Field(default=None, env="POSTGRES_PASSWORD")
    
    # 连接池配置
    pool_size: int = Field(default=10, env="POSTGRES_POOL_SIZE")
    max_overflow: int = Field(default=20, env="POSTGRES_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="POSTGRES_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, env="POSTGRES_POOL_RECYCLE")
    
    # SSL配置
    ssl_mode: str = Field(default="prefer", env="POSTGRES_SSL_MODE")
    
    @property
    def database_url(self) -> str:
        """生成数据库连接URL"""
        if self.password:
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
        else:
            return f"postgresql://{self.user}@{self.host}:{self.port}/{self.db}"


class RedisConfig(BaseSettings):
    """Redis 配置"""
    
    model_config = SettingsConfigDict(
        env_file=need_load_dev_env,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    db: int = Field(default=0, alias="REDIS_DB")
    password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    
    # 连接池配置
    max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")
    
    # 缓存配置
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1小时
    session_ttl: int = Field(default=86400, env="SESSION_TTL")  # 24小时
    
    @property
    def redis_url(self) -> str:
        """生成Redis连接URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        else:
            return f"redis://{self.host}:{self.port}/{self.db}"


class AgentConfig(BaseSettings):
    """智能体配置"""
    
    model_config = SettingsConfigDict(
        env_file=need_load_dev_env,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # 查询分解
    max_sub_questions: int = Field(default=5, env="MAX_SUB_QUESTIONS")
    min_sub_questions: int = Field(default=2, env="MIN_SUB_QUESTIONS")
    max_iterations: int = Field(default=10, env="MAX_ITERATIONS")
    
    # 搜索图
    max_graph_depth: int = Field(default=3, env="MAX_GRAPH_DEPTH")
    max_graph_nodes: int = Field(default=20, env="MAX_GRAPH_NODES")
    
    # 响应生成
    max_response_length: int = Field(default=2000, env="MAX_RESPONSE_LENGTH")
    include_references: bool = Field(default=True, env="INCLUDE_REFERENCES")
    
    # 流式响应
    enable_streaming: bool = Field(default=True, env="ENABLE_STREAMING")
    stream_chunk_size: int = Field(default=50, env="STREAM_CHUNK_SIZE")
    
    # 超时配置
    agent_timeout: int = Field(default=300, env="AGENT_TIMEOUT")  # 5分钟
    search_timeout: int = Field(default=60, env="SEARCH_TIMEOUT")  # 1分钟


class Settings(BaseSettings):
    """主配置类"""
    
    model_config = SettingsConfigDict(
        env_file=need_load_dev_env,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # 子配置
    llm: LLMConfig = Field(default_factory=LLMConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    postgres: PostgreSQLConfig = Field(default_factory=PostgreSQLConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    
    # 全局配置
    app_name: str = Field(default="MindSearch LangChain", env="APP_NAME")
    version: str = Field(default="0.1.0", env="VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    def __init__(self, **kwargs):
        # 提取_env_file参数
        env_file = kwargs.get('_env_file', '.env')
        
        # 为所有子配置传递_env_file参数
        if 'llm' not in kwargs:
            kwargs['llm'] = LLMConfig(_env_file=env_file)
        if 'search' not in kwargs:
            kwargs['search'] = SearchConfig(_env_file=env_file)
        if 'server' not in kwargs:
            kwargs['server'] = ServerConfig(_env_file=env_file)
        if 'postgres' not in kwargs:
            kwargs['postgres'] = PostgreSQLConfig(_env_file=env_file)
        if 'redis' not in kwargs:
            kwargs['redis'] = RedisConfig(_env_file=env_file)
        if 'agent' not in kwargs:
            kwargs['agent'] = AgentConfig(_env_file=env_file)
            
        super().__init__(**kwargs)


# 全局配置实例
settings = None
current_environment = None

def _get_environment_from_config() -> str:
    """从配置文件中获取环境变量ENVIRONMENT

    说实在的，写的有点太鸡肋了。食之无味，弃之可惜。就是为了获取一个简单的配置环境信息，没必要搞得这么麻烦。
    要不自定义好，要不写歌接口简单的实现一下。
    
    优先级：
    1. 系统环境变量 ENVIRONMENT
    2. .dev_env 文件中的 ENVIRONMENT
    3. .env 文件中的 ENVIRONMENT  
    4. 默认值 'development'
    """
    # 首先检查系统环境变量
    env_from_system = os.getenv('.ENVIRONMENT')
    # from langchain_rebuild.settings.dev_settings import *
    if env_from_system:
        return env_from_system
    
    # 然后检查 .dev_env 文件
    dev_env_path = '/Users/weifuqiang/Desktop/llmsearch/MindSearch-myself/langchain_rebuild/.dev_env'
    # dev_env_path = '.dev_env'

    if os.path.exists(dev_env_path):
        dev_env_vars = dotenv_values(dev_env_path)
        env_from_dev = dev_env_vars.get('ENVIRONMENT')
        if env_from_dev:
            return env_from_dev
    
    # 最后检查 .env 文件
    env_path = '.env'
    if os.path.exists(env_path):
        env_vars = dotenv_values(env_path)
        env_from_file = env_vars.get('ENVIRONMENT')
        if env_from_file:
            return env_from_file
    
    # 默认返回 development
    return 'development'


def _get_settings(environment: str = None):
    global settings, current_environment
    
    # 如果没有指定环境，从配置文件中获取
    if environment is None:
        environment = _get_environment_from_config()
    
    # 如果环境发生变化，重新创建settings
    #todo 这理写的就有问题。又重复，又没有实现接口的性质。要是再来一个新的配置文件，难道再加一个配置吗？是个问题，但是不是现在的问题。
    if settings is None or current_environment != environment:
        if environment == 'development':
            env_file = '.dev_env'
        else:
            env_file = '.env'
        
        settings = Settings(_env_file=env_file)
        current_environment = environment
        
    # 这里返回的是settings的对象。可以通过点点形式将属性都获取出来。
    return settings


def get_settings(environment: str = None) -> Settings:
    """获取配置实例"""
    return _get_settings(environment)


def get_config(environment: str = None) -> Settings:
    """获取全局配置实例"""
    return _get_settings(environment)

def get_llm_config(environment: str = None) -> LLMConfig:
    """获取LLM配置"""
    return _get_settings(environment).llm

def get_search_config(environment: str = None) -> SearchConfig:
    """获取搜索配置"""
    return _get_settings(environment).search

def get_server_config(environment: str = None) -> ServerConfig:
    """获取服务器配置"""
    return _get_settings(environment).server

def get_postgres_config(environment: str = None) -> PostgreSQLConfig:
    """获取PostgreSQL配置"""
    return _get_settings(environment).postgres

def get_redis_config(environment: str = None) -> RedisConfig:
    """获取Redis配置"""
    return _get_settings(environment).redis

def get_agent_config(environment: str = None) -> AgentConfig:
    """获取智能体配置"""
    return _get_settings(environment).agent


def reload_settings() -> Settings:
    """重新加载配置"""
    global settings
    settings = None  # 重置为None，下次调用时会重新创建
    return _get_settings()