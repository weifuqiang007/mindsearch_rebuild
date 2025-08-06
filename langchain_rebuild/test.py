# # from dotenv import load_dotenv
# # import os
# # import sys
# #
# # print(os.path.dirname(os.path.abspath(__file__)))
# # sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# # from datetime import datetime
# # from typing import List, Dict, Any
# #
# # # 避免导入core模块，因为它会触发相对导入问题
# # # 当直接运行脚本时，Python将其视为主模块，相对导入会失败
# # try:
# #     # 尝试直接导入search_tools模块，避免通过core.__init__.py
# #     import core.search_tools as search_tools
# #     import config
# #
# #     SearchToolManager = search_tools.SearchToolManager
# #     SearchEngine = search_tools.SearchEngine
# #     SearchResult = search_tools.SearchResult
# #     get_search_manager = search_tools.get_search_manager
# #     get_settings = config.get_settings
# #
# #     print("✅ 成功导入搜索工具")
# # except ImportError as e:
# #     print(f"❌ 导入失败: {e}")
# #     print("\n💡 解决方案:")
# #     print("1. 使用 'python -m langchain_rebuild.test' 运行（作为模块）")
# #     print("2. 或者将此文件移到项目根目录外")
# #     print("3. 或者修改导入方式避免相对导入问题")
# #     sys.exit(1)
# #
# # class TraditionalSearchExample:
# #     def __init__(self):
# #         pass
# #
# #     def search_with_requests(self, query: str) -> Dict[str, Any]:
# #         pass
# #
# # class SearchEngineTest:
# #     def __init__(self):
# #         self.settings = get_settings()
# #         self.search_manager = get_search_manager()
# #         self.traditional_search = TraditionalSearchExample()
# #
# #     def print_config_info(self):
# #         print("=" * 60)
# #         print("搜索引擎配置信息")
# #         print("=" * 60)
# #
# #         search_config = self.settings.search
# #         print(f"默认搜索引擎: {search_config.default_engine}")
# #         print(f"Google API Key: {'已配置' if search_config.google_api_key else '未配置'}")
# #         print(f"Google 搜索引擎ID: {'已配置' if search_config.google_search_engine_id else '未配置'}")
# #         print(f"Bing API Key: {'已配置' if search_config.bing_api_key else '未配置'}")
# #         print(f"Serper API Key: {'已配置' if search_config.serper_api_key else '未配置'}")
# #
# #         available_engines = self.search_manager.list_engines()
# #         print(f"可用搜索引擎: {[engine.value for engine in available_engines]}")
# #         print()
# #         pass
# #
# # def main():
# #     """主测试函数"""
# #     print("🚀 搜索引擎测试开始")
# #     print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
# #
# #     # 初始化测试
# #     test = SearchEngineTest()
# #
# #     test.print_config_info()
#
# # from dotenv import load_dotenv, dotenv_values
# #
# # env_file = ".dev_env"
# # env_path = ".dev_env"
# #
# # dev_env_vars = dotenv_values(env_path)
# # print(dev_env_vars)
# from pydantic_settings import BaseSettings, SettingsConfigDict
# need_load_dev_env = ".dev_env"
# from pydantic import Field
# from config import LLMConfig, SearchConfig, ServerConfig, PostgreSQLConfig, RedisConfig, AgentConfig
#
#
# class Settings(BaseSettings):
#     """主配置类"""
#
#     model_config = SettingsConfigDict(
#         env_file=need_load_dev_env,
#         env_file_encoding="utf-8",
#         case_sensitive=False,
#         extra="ignore"
#     )
#
#     # 子配置
#     llm: LLMConfig = Field(default_factory=LLMConfig)
#     search: SearchConfig = Field(default_factory=SearchConfig)
#     server: ServerConfig = Field(default_factory=ServerConfig)
#     postgres: PostgreSQLConfig = Field(default_factory=PostgreSQLConfig)
#     redis: RedisConfig = Field(default_factory=RedisConfig)
#     agent: AgentConfig = Field(default_factory=AgentConfig)
#
#     # 全局配置
#     app_name: str = Field(default="MindSearch LangChain", env="APP_NAME")
#     version: str = Field(default="0.1.0", env="VERSION")
#     environment: str = Field(default="development", env="ENVIRONMENT")
#
#     def __init__(self, **kwargs):
#         # 提取_env_file参数
#         env_file = kwargs.get('_env_file', '.env')
#
#         # 为所有子配置传递_env_file参数
#         if 'llm' not in kwargs:
#             kwargs['llm'] = LLMConfig(_env_file=env_file)
#         if 'search' not in kwargs:
#             kwargs['search'] = SearchConfig(_env_file=env_file)
#         if 'server' not in kwargs:
#             kwargs['server'] = ServerConfig(_env_file=env_file)
#         if 'postgres' not in kwargs:
#             kwargs['postgres'] = PostgreSQLConfig(_env_file=env_file)
#         if 'redis' not in kwargs:
#             kwargs['redis'] = RedisConfig(_env_file=env_file)
#         if 'agent' not in kwargs:
#             kwargs['agent'] = AgentConfig(_env_file=env_file)
#
#         super().__init__(**kwargs)
#
#
# if __name__ == "__main__":
#     settings = Settings(_env_file=".dev_env")
#     print(settings.llm)
# 定义llm的管理器
# from abc import ABC, abstractmethod
# from enum import Enum
# from typing import Optional, Dict, Any, List, AsyncGenerator
#
# import asyncio
#
# # 这个包是干什么用的
# from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
# # from langchain_community.chat_models import ChatOpenAI as CommunityChatOpenAI
# from langchain_openai import ChatOpenAI
#
#
# try:
#     from ..config import get_settings
# except ImportError:
#     # 当直接运行脚本时，相对导入会失败，使用绝对导入
#     from langchain_rebuild.config import get_settings
#
#
# class LLMProvider(Enum):
#     """LLM 提供商枚举"""
#     OPENAI = "openai"
#     ANTHROPIC = "anthropic"
#     SILICONFLOW = "siliconflow"
#     LOCAL = "local"
#
# class BaseLLMWrapper(ABC):
#     """LLM包装器基类"""
#
#     def __init__(self, provider: LLMProvider, **kwargs):
#         self.provider = provider
#         self.config = kwargs
#         self._llm = None
#         self._initialize()
#
#     @abstractmethod
#     def _initialize(self):
#         """初始化LLM实例"""
#         pass
#
#     @abstractmethod
#     async def agenerate(self, messages: List[BaseMessage], **kwargs) -> str:
#         """异步生成响应"""
#         pass
#
#     @abstractmethod
#     async def astream(self, messages: List[BaseMessage], **kwargs) -> AsyncGenerator[str, None]:
#         """异步流式生成响应"""
#         pass
#
#     def generate(self, messages: List[BaseMessage], **kwargs) -> str:
#         """同步生成响应"""
#         return asyncio.run(self.agenerate(messages, **kwargs))
#
#
# class SiliconFlowWrapper(BaseLLMWrapper):
#     """SiliconFlow LLM 包装器"""
#
#     def _initialize(self):
#         settings = get_settings()
#         self._llm = ChatOpenAI(
#             api_key=settings.llm.siliconflow_api_key,
#             base_url=settings.llm.siliconflow_base_url,
#             model=settings.llm.siliconflow_model,
#             temperature=settings.llm.temperature,
#             max_tokens=settings.llm.max_tokens,
#             timeout=settings.llm.timeout,
#             streaming=True,
#             **self.config
#         )
#
#     async def agenerate(self, messages: List[BaseMessage], **kwargs) -> str:
#         """异步生成响应"""
#         response = await self._llm.agenerate(messages, **kwargs)
#         return response.generations[0][0].text
#
#     async def astream(self, messages: List[BaseMessage], **kwargs) -> AsyncGenerator[str, None]:
#         """异步流式生成响应"""
#         async for chunk in self._llm.astream(messages, **kwargs):
#             if chunk.content:
#                 yield chunk.content
#
#
# llm = SiliconFlowWrapper(provider=LLMProvider.SILICONFLOW)
# messages = [HumanMessage(content="Hello, how are you?")]
# # messages = [BaseMessage(content="Hello, how are you?", type="human")]
# print(asyncio.run(llm.agenerate(messages)))  # 同步调用测试


from abc import ABC, abstractmethod
from enum import Enum
from typing import List, AsyncGenerator
import asyncio
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage


try:
    from ..config import get_settings
except ImportError:
    # 当直接运行脚本时，相对导入会失败，使用绝对导入
    from langchain_rebuild.config import get_settings


class LLMProvider(Enum):
    """LLM 提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    SILICONFLOW = "siliconflow"
    LOCAL = "local"

class BaseLLMWrapper(ABC):
    """LLM包装器基类"""

    def __init__(self, provider: LLMProvider, **kwargs):
        self.provider = provider
        self.config = kwargs
        self._llm = None
        self._initialize()

    @abstractmethod
    def _initialize(self):
        """初始化LLM实例"""
        pass

    @abstractmethod
    async def agenerate(self, messages: List[BaseMessage], **kwargs) -> str:
        """异步生成响应"""
        pass

    @abstractmethod
    async def astream(self, messages: List[BaseMessage], **kwargs) -> AsyncGenerator[str, None]:
        """异步流式生成响应"""
        pass

    def generate(self, messages: List[BaseMessage], **kwargs) -> str:
        """同步生成响应"""
        return asyncio.run(self.agenerate(messages, **kwargs))


class SiliconFlowWrapper(BaseLLMWrapper):
    def _initialize(self):
        settings = get_settings()
        self._llm = ChatOpenAI(
            api_key=settings.llm.siliconflow_api_key,
            base_url=settings.llm.siliconflow_base_url,
            model=settings.llm.siliconflow_model,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
            timeout=settings.llm.timeout,
            streaming=True,
            **self.config
        )

    # agenerate 需要接收的是一个 列表的列表 ([messages])，因为 LangChain 设计如此（支持批量生成）。
    async def agenerate(self, messages: List[BaseMessage], **kwargs) -> str:
        # 验证消息格式
        if not all(isinstance(msg, (HumanMessage, AIMessage, SystemMessage)) for msg in messages):
            raise ValueError("Messages must be HumanMessage/AIMessage/SystemMessage")

        response = await self._llm.agenerate([messages], **kwargs)  # ✅ 注意需要 [messages]
        return response.generations[0][0].text

    async def astream(self, messages: List[BaseMessage], **kwargs) -> AsyncGenerator[str, None]:
        async for chunk in self._llm.astream(messages, **kwargs):
            if chunk.content:
                yield chunk.content


# 测试
llm = SiliconFlowWrapper(provider=LLMProvider.SILICONFLOW)
messages = [HumanMessage(content="python中多线程和协程是什么呀？语法怎么写？有什么区别？能不能给写一些代码示例？尽量用通俗易懂和举例子、做对比的方式进行讲解。"), SystemMessage(content="你是一个开发的专家，尤其是在AI编程领域有非常丰富的经验，你需要非常细致的将我的问题进行回答。而且需要配合上一些代码示例进行讲解回答")]  # ✅ 标准消息格式
# print(asyncio.run(llm.agenerate(messages)))
# print(asyncio.run(llm.astream(messages)))


async def run_stream():
    llm = SiliconFlowWrapper(provider=LLMProvider.SILICONFLOW)
    messages = [HumanMessage(content="python中多线程和协程是什么呀？语法怎么写？有什么区别？能不能给写一些代码示例？尽量用通俗易懂和举例子、做对比的方式进行讲解。"),
                SystemMessage(content="你是一个开发的专家，尤其是在AI编程领域有非常丰富的经验，你需要非常细致的将我的问题进行回答。而且需要配合上一些代码示例进行讲解回答")]  # ✅ 标准消息格式
    # astream() 本身是异步生成器，必须用 async for 消费。
    # 任何包含 async for 或 await 的代码块必须位于 async def 函数内（Python的强制要求）。
    async for chunk in llm.astream(messages):
        print(chunk, end="", flush=True) # 实时打印流式结果

asyncio.run(run_stream())


