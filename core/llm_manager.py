"""LLM 管理器

统一管理不同的语言模型提供商，提供标准化的调用接口
"""

import asyncio
from typing import Optional, Dict, Any, List, AsyncGenerator
from abc import ABC, abstractmethod
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.base import BaseCallbackHandler

try:
    from config import get_settings
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import get_settings


class LLMProvider(Enum):
    """LLM 提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    SILICONFLOW = "siliconflow"
    LOCAL = "local"


class StreamingCallbackHandler(BaseCallbackHandler):
    """流式响应回调处理器"""
    
    def __init__(self):
        self.tokens = []
        self.finished = False
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """处理新的token"""
        self.tokens.append(token)
    
    def on_llm_end(self, response, **kwargs) -> None:
        """LLM调用结束"""
        self.finished = True
    
    def get_tokens(self) -> List[str]:
        """获取所有tokens"""
        return self.tokens.copy()
    
    def clear(self):
        """清空tokens"""
        self.tokens.clear()
        self.finished = False


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


class OpenAIWrapper(BaseLLMWrapper):
    """OpenAI LLM 包装器"""
    
    def _initialize(self):
        settings = get_settings()
        self._llm = ChatOpenAI(
            api_key=settings.llm.openai_api_key,
            base_url=settings.llm.openai_base_url,
            model=settings.llm.openai_model,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
            timeout=settings.llm.timeout,
            streaming=True,
            **self.config
        )
    
    async def agenerate(self, messages: List[BaseMessage], **kwargs) -> str:
        """异步生成响应"""
        response = await self._llm.agenerate([messages], **kwargs)
        return response.generations[0][0].text
    
    async def astream(self, messages: List[BaseMessage], **kwargs) -> AsyncGenerator[str, None]:
        """异步流式生成响应"""
        async for chunk in self._llm.astream(messages, **kwargs):
            if chunk.content:
                yield chunk.content


class AnthropicWrapper(BaseLLMWrapper):
    """Anthropic LLM 包装器"""
    
    def _initialize(self):
        settings = get_settings()
        self._llm = ChatAnthropic(
            api_key=settings.llm.anthropic_api_key,
            model=settings.llm.anthropic_model,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
            timeout=settings.llm.timeout,
            streaming=True,
            **self.config
        )
    
    async def agenerate(self, messages: List[BaseMessage], **kwargs) -> str:
        """异步生成响应"""
        response = await self._llm.agenerate([messages], **kwargs)
        return response.generations[0][0].text
    
    async def astream(self, messages: List[BaseMessage], **kwargs) -> AsyncGenerator[str, None]:
        """异步流式生成响应"""
        async for chunk in self._llm.astream(messages, **kwargs):
            if chunk.content:
                yield chunk.content


class SiliconFlowWrapper(BaseLLMWrapper):
    """SiliconFlow LLM 包装器"""
    
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
    
    async def agenerate(self, messages: List[BaseMessage], **kwargs) -> str:
        """异步生成响应"""
        # 验证消息格式
        if not all(isinstance(msg, (HumanMessage, AIMessage, SystemMessage)) for msg in messages):
            raise ValueError("Messages must be HumanMessage/AIMessage/SystemMessage")
        response = await self._llm.agenerate([messages], **kwargs)
        return response.generations[0][0].text
    
    async def astream(self, messages: List[BaseMessage], **kwargs) -> AsyncGenerator[str, None]:
        """异步流式生成响应"""
        async for chunk in self._llm.astream(messages, **kwargs):
            if chunk.content:
                yield chunk.content


class LLMManager:
    """LLM 管理器
    
    统一管理不同的语言模型提供商，提供标准化的调用接口
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._providers: Dict[LLMProvider, BaseLLMWrapper] = {}
        self._default_provider = LLMProvider(self.settings.llm.default_provider)
        self._initialize_providers()
    
    def _initialize_providers(self):
        """初始化可用的LLM提供商"""
        # # OpenAI
        # if self.settings.llm.openai_api_key:
        #     self._providers[LLMProvider.OPENAI] = OpenAIWrapper(LLMProvider.OPENAI)
        #
        # # Anthropic
        # if self.settings.llm.anthropic_api_key:
        #     self._providers[LLMProvider.ANTHROPIC] = AnthropicWrapper(LLMProvider.ANTHROPIC)
        
        # SiliconFlow
        if self.settings.llm.siliconflow_api_key:
            self._providers[LLMProvider.SILICONFLOW] = SiliconFlowWrapper(LLMProvider.SILICONFLOW)
        
        # if not self._providers:
        #     raise ValueError("No LLM providers configured. Please set API keys in environment variables.")
    
    def get_provider(self, provider: Optional[LLMProvider] = None) -> BaseLLMWrapper:
        """获取LLM提供商"""
        if provider is None:
            provider = self._default_provider
        
        if provider not in self._providers:
            available = list(self._providers.keys())
            raise ValueError(f"Provider {provider} not available. Available providers: {available}")
        
        return self._providers[provider]
    
    def list_providers(self) -> List[LLMProvider]:
        """列出可用的提供商"""
        return list(self._providers.keys())
    
    async def agenerate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> str:
        """异步生成响应"""
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        messages.append(HumanMessage(content=prompt))
        
        llm_wrapper = self.get_provider(provider)
        return await llm_wrapper.agenerate(messages, **kwargs)
    
    async def astream(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """异步流式生成响应"""
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        messages.append(HumanMessage(content=prompt))
        
        llm_wrapper = self.get_provider(provider)
        async for chunk in llm_wrapper.astream(messages, **kwargs):
            yield chunk
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> str:
        """同步生成响应"""
        return asyncio.run(self.agenerate(prompt, system_prompt, provider, **kwargs))
    
    async def achat(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> str:
        """异步对话
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}, ...]
            provider: LLM提供商
            **kwargs: 其他参数
        """
        langchain_messages = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                raise ValueError(f"Unknown role: {role}")
        
        llm_wrapper = self.get_provider(provider)
        return await llm_wrapper.agenerate(langchain_messages, **kwargs)
    
    async def astream_chat(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """异步流式对话"""
        langchain_messages = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                raise ValueError(f"Unknown role: {role}")
        
        llm_wrapper = self.get_provider(provider)
        async for chunk in llm_wrapper.astream(langchain_messages, **kwargs):
            yield chunk


# 全局LLM管理器实例
_llm_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """获取全局LLM管理器实例"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager


def reset_llm_manager():
    """重置LLM管理器（用于测试）"""
    global _llm_manager
    _llm_manager = None