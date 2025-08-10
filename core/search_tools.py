"""搜索工具管理器

支持多种搜索引擎：Bing、Google、DuckDuckGo等
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, AsyncGenerator
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# 支持两种导入方式：相对导入（包内使用）和绝对导入（直接运行时）
try:
    from ..config import get_settings
except ImportError:
    # 当直接运行脚本时，相对导入会失败，使用绝对导入
    import sys
    import os
    from pathlib import Path
    
    # 添加项目根目录到Python路径
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    sys.path.insert(0, str(project_root))
    
    from config import get_settings


class SearchEngine(Enum):
    """搜索引擎枚举"""
    BING = "bing"
    GOOGLE = "google"
    DUCKDUCKGO = "duckduckgo"
    SERPER = "serper"


@dataclass
class SearchResult:
    """搜索结果数据类"""
    title: str
    url: str
    snippet: str
    source: str = ""
    timestamp: Optional[datetime] = None
    score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "score": self.score
        }


class BaseSearchEngine(ABC):
    """搜索引擎基类"""
    
    def __init__(self, engine: SearchEngine, **kwargs):
        self.engine = engine
        self.config = kwargs
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """执行搜索"""
        pass
    
    @abstractmethod
    def _parse_results(self, response_data: Dict[str, Any]) -> List[SearchResult]:
        """解析搜索结果"""
        pass


class BingSearchEngine(BaseSearchEngine):
    """Bing 搜索引擎"""
    
    def __init__(self, **kwargs):
        super().__init__(SearchEngine.BING, **kwargs)
        self.settings = get_settings()
        self.api_key = self.settings.search.bing_api_key
        self.endpoint = self.settings.search.bing_endpoint
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """执行Bing搜索"""
        if not self.api_key:
            raise ValueError("Bing API key not configured")
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "User-Agent": "Mozilla/5.0 (compatible; LangChain-MindSearch/1.0)"
        }
        
        params = {
            "q": query,
            "count": min(num_results, 50),
            "offset": 0,
            "mkt": "zh-CN",
            "safesearch": "Moderate"
        }
        
        url = f"{self.endpoint}/v7.0/search"
        
        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                raise Exception(f"Bing search failed: {response.status} - {await response.text()}")
            
            data = await response.json()
            return self._parse_results(data)
    
    def _parse_results(self, response_data: Dict[str, Any]) -> List[SearchResult]:
        """解析Bing搜索结果"""
        results = []
        
        web_pages = response_data.get("webPages", {}).get("value", [])
        
        for item in web_pages:
            result = SearchResult(
                title=item.get("name", ""),
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
                source="bing",
                timestamp=datetime.now()
            )
            results.append(result)
        
        return results


class GoogleSearchEngine(BaseSearchEngine):
    """Google 搜索引擎（通过Custom Search API）"""
    
    def __init__(self, **kwargs):
        super().__init__(SearchEngine.GOOGLE, **kwargs)
        self.settings = get_settings()
        self.api_key = self.settings.search.google_api_key
        self.search_engine_id = self.settings.search.google_cse_id
        self.endpoint = "https://www.googleapis.com/customsearch/v1"
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """执行Google搜索"""
        if not self.api_key or not self.search_engine_id:
            raise ValueError("Google API key or Search Engine ID not configured")
        
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10),
            "start": 1,
            "lr": "lang_zh-CN"
        }
        
        async with self.session.get(self.endpoint, params=params) as response:
            if response.status != 200:
                raise Exception(f"Google search failed: {response.status} - {await response.text()}")
            
            data = await response.json()
            return self._parse_results(data)
    
    def _parse_results(self, response_data: Dict[str, Any]) -> List[SearchResult]:
        """解析Google搜索结果"""
        results = []
        
        items = response_data.get("items", [])
        
        for item in items:
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                source="google",
                timestamp=datetime.now()
            )
            results.append(result)
        
        return results


class DuckDuckGoSearchEngine(BaseSearchEngine):
    """DuckDuckGo 搜索引擎（免费API）"""
    
    def __init__(self, **kwargs):
        super().__init__(SearchEngine.DUCKDUCKGO, **kwargs)
        self.endpoint = "https://api.duckduckgo.com/"
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """执行DuckDuckGo搜索"""
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        }
        
        async with self.session.get(self.endpoint, params=params) as response:
            if response.status != 200:
                raise Exception(f"DuckDuckGo search failed: {response.status} - {await response.text()}")
            
            data = await response.json()
            return self._parse_results(data)
    
    def _parse_results(self, response_data: Dict[str, Any]) -> List[SearchResult]:
        """解析DuckDuckGo搜索结果"""
        results = []
        
        # DuckDuckGo的结果结构
        related_topics = response_data.get("RelatedTopics", [])
        
        for item in related_topics[:10]:  # 限制结果数量
            if isinstance(item, dict) and "Text" in item:
                result = SearchResult(
                    title=item.get("Text", "")[:100],  # 截取标题
                    url=item.get("FirstURL", ""),
                    snippet=item.get("Text", ""),
                    source="duckduckgo",
                    timestamp=datetime.now()
                )
                results.append(result)
        
        return results


class SerperSearchEngine(BaseSearchEngine):
    """Serper 搜索引擎"""
    
    def __init__(self, **kwargs):
        super().__init__(SearchEngine.SERPER, **kwargs)
        self.settings = get_settings()
        self.api_key = self.settings.search.serper_api_key
        self.endpoint = "https://google.serper.dev/search"
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """执行Serper搜索"""
        if not self.api_key:
            raise ValueError("Serper API key not configured")
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": min(num_results, 100),
            "hl": "zh-cn",
            "gl": "cn"
        }
        
        async with self.session.post(self.endpoint, headers=headers, json=payload) as response:
            if response.status != 200:
                raise Exception(f"Serper search failed: {response.status} - {await response.text()}")
            
            data = await response.json()
            return self._parse_results(data)
    
    def _parse_results(self, response_data: Dict[str, Any]) -> List[SearchResult]:
        """解析Serper搜索结果"""
        results = []
        
        organic = response_data.get("organic", [])
        
        for item in organic:
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                source="serper",
                timestamp=datetime.now()
            )
            results.append(result)
        
        return results


class SearchToolManager:
    """搜索工具管理器
    
    统一管理不同的搜索引擎，提供标准化的搜索接口
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._engines: Dict[SearchEngine, BaseSearchEngine] = {}
        self._default_engine = SearchEngine(self.settings.search.default_engine)
        self._initialize_engines()
    
    def _initialize_engines(self):
        """初始化可用的搜索引擎"""
        # Bing
        if self.settings.search.bing_api_key:
            self._engines[SearchEngine.BING] = BingSearchEngine()
        
        # Google
        if self.settings.search.google_api_key and self.settings.search.google_cse_id:
            self._engines[SearchEngine.GOOGLE] = GoogleSearchEngine()
        
        # DuckDuckGo (免费，总是可用)
        self._engines[SearchEngine.DUCKDUCKGO] = DuckDuckGoSearchEngine()
        
        # Serper
        if self.settings.search.serper_api_key:
            self._engines[SearchEngine.SERPER] = SerperSearchEngine()
        
        if not self._engines:
            raise ValueError("No search engines configured")
    
    def get_engine(self, engine: Optional[SearchEngine] = None) -> BaseSearchEngine:
        """获取搜索引擎"""
        if engine is None:
            engine = self._default_engine
        
        if engine not in self._engines:
            available = list(self._engines.keys())
            raise ValueError(f"Search engine {engine} not available. Available engines: {available}")
        
        return self._engines[engine]
    
    def list_engines(self) -> List[SearchEngine]:
        """列出可用的搜索引擎"""
        return list(self._engines.keys())
    
    async def search(
        self, 
        query: str, 
        num_results: int = 10,
        engine: Optional[SearchEngine] = None
    ) -> List[SearchResult]:
        """执行搜索"""
        search_engine = self.get_engine(engine)
        
        async with search_engine:
            results = await search_engine.search(query, num_results)
            
            # 添加搜索评分（简单的相关性评分）
            for i, result in enumerate(results):
                result.score = 1.0 - (i * 0.1)  # 简单的位置评分
            
            return results
    
    async def multi_engine_search(
        self,
        query: str,
        num_results: int = 10,
        engines: Optional[List[SearchEngine]] = None
    ) -> Dict[SearchEngine, List[SearchResult]]:
        """多引擎搜索"""
        if engines is None:
            engines = list(self._engines.keys())
        
        results = {}
        tasks = []
        
        for engine in engines:
            if engine in self._engines:
                task = self.search(query, num_results, engine)
                tasks.append((engine, task))
        
        # 并发执行搜索
        completed_tasks = await asyncio.gather(
            *[task for _, task in tasks], 
            return_exceptions=True
        )
        
        for (engine, _), result in zip(tasks, completed_tasks):
            if isinstance(result, Exception):
                print(f"Search failed for {engine}: {result}")
                results[engine] = []
            else:
                results[engine] = result
        
        return results
    
    async def aggregate_search(
        self,
        query: str,
        num_results: int = 10,
        engines: Optional[List[SearchEngine]] = None
    ) -> List[SearchResult]:
        """聚合搜索结果"""
        multi_results = await self.multi_engine_search(query, num_results, engines)
        
        # 合并和去重
        all_results = []
        seen_urls = set()
        
        for engine, results in multi_results.items():
            for result in results:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    all_results.append(result)
        
        # 按评分排序
        all_results.sort(key=lambda x: x.score, reverse=True)
        
        return all_results[:num_results]


# 全局搜索工具管理器实例
_search_manager: Optional[SearchToolManager] = None


def get_search_manager() -> SearchToolManager:
    """获取全局搜索工具管理器实例"""
    global _search_manager
    if _search_manager is None:
        _search_manager = SearchToolManager()
    return _search_manager


def reset_search_manager():
    """重置搜索工具管理器（用于测试）"""
    global _search_manager
    _search_manager = None