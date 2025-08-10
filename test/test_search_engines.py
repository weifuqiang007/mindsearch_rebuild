#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索引擎测试用例

本测试文件演示了项目中搜索引擎配置的使用方法，
包括Google搜索和DuckDuckGo搜索的对比测试，
以及与传统requests方法的区别说明。
"""

import asyncio
import sys
import os
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 尝试直接导入
    import core.search_tools as search_tools
    import config
    
    SearchToolManager = search_tools.SearchToolManager
    SearchEngine = search_tools.SearchEngine
    SearchResult = search_tools.SearchResult
    get_search_manager = search_tools.get_search_manager
    get_settings = config.get_settings
    
except ImportError as e:
    print(f"导入错误: {e}")
    print("尝试使用简化版本...")
    
    # 如果导入失败，创建简化版本用于演示
    import requests
    from urllib.parse import quote
    from enum import Enum
    from dataclasses import dataclass
    from datetime import datetime
    class SearchEngine(Enum):
        GOOGLE = "google"
        DUCKDUCKGO = "duckduckgo"
    
    @dataclass
    class SearchResult:
        title: str
        url: str
        snippet: str
        source: str = ""
        timestamp: Optional[datetime] = None
        score: float = 0.0
    
    class SimpleSearchManager:
        def __init__(self):
            pass
        
        def list_engines(self):
            return [SearchEngine.DUCKDUCKGO]
        
        async def search(self, query: str, num_results: int = 10, engine=None):
            # 简化的DuckDuckGo搜索
            try:
                encoded_query = quote(query)
                url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for i, item in enumerate(data.get("RelatedTopics", [])[:num_results]):
                    if isinstance(item, dict) and "Text" in item:
                        result = SearchResult(
                            title=item.get("Text", "")[:100],
                            url=item.get("FirstURL", ""),
                            snippet=item.get("Text", ""),
                            source="duckduckgo",
                            timestamp=datetime.now(),
                            score=1.0 - (i * 0.1)
                        )
                        results.append(result)
                
                return results
            except Exception as e:
                print(f"搜索失败: {e}")
                return []
        
        async def multi_engine_search(self, query: str, num_results: int = 10, engines=None):
            results = await self.search(query, num_results)
            return {SearchEngine.DUCKDUCKGO: results}
        
        async def aggregate_search(self, query: str, num_results: int = 10, engines=None):
            return await self.search(query, num_results)
    
    def get_search_manager():
        return SimpleSearchManager()
    
    class SimpleSettings:
        def __init__(self):
            self.search = SimpleSearchConfig()
    
    class SimpleSearchConfig:
        def __init__(self):
            self.default_engine = "duckduckgo"
            self.google_api_key = None
            self.google_search_engine_id = None
            self.bing_api_key = None
            self.serper_api_key = None
    
    def get_settings():
        return SimpleSettings()
    
    print("✅ 使用简化版本进行演示")

# 传统requests方法示例（用于对比）
import requests
from urllib.parse import quote


class TraditionalSearchExample:
    """传统requests搜索方法示例"""
    
    def search_with_requests(self, query: str) -> Dict[str, Any]:
        """使用传统requests方法搜索（以DuckDuckGo为例）"""
        try:
            # 构建搜索URL
            encoded_query = quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            # 发送请求
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # 解析结果
            data = response.json()
            
            # 手动处理结果
            results = []
            for item in data.get("RelatedTopics", [])[:5]:
                if isinstance(item, dict) and "Text" in item:
                    results.append({
                        "title": item.get("Text", "")[:100],
                        "url": item.get("FirstURL", ""),
                        "snippet": item.get("Text", "")
                    })
            
            return {
                "success": True,
                "results": results,
                "method": "traditional_requests"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "method": "traditional_requests"
            }


class SearchEngineTest:
    """搜索引擎测试类"""
    
    def __init__(self):
        self.settings = get_settings()
        self.search_manager = get_search_manager()
        self.traditional_search = TraditionalSearchExample()
    
    def print_config_info(self):
        """打印搜索引擎配置信息"""
        print("=" * 60)
        print("搜索引擎配置信息")
        print("=" * 60)
        
        search_config = self.settings.search
        print(f"默认搜索引擎: {search_config.default_engine}")
        print(f"Google API Key: {'已配置' if search_config.google_api_key else '未配置'}")
        print(f"Google 搜索引擎ID: {'已配置' if search_config.google_search_engine_id else '未配置'}")
        print(f"Bing API Key: {'已配置' if search_config.bing_api_key else '未配置'}")
        print(f"Serper API Key: {'已配置' if search_config.serper_api_key else '未配置'}")
        
        available_engines = self.search_manager.list_engines()
        print(f"可用搜索引擎: {[engine.value for engine in available_engines]}")
        print()
    
    def print_search_results(self, results: List[SearchResult], engine_name: str):
        """打印搜索结果"""
        print(f"\n--- {engine_name} 搜索结果 ---")
        if not results:
            print("没有找到结果")
            return
        
        for i, result in enumerate(results[:5], 1):
            print(f"{i}. 标题: {result.title}")
            print(f"   链接: {result.url}")
            print(f"   摘要: {result.snippet[:100]}...")
            print(f"   来源: {result.source}")
            print(f"   评分: {result.score:.2f}")
            print()
    
    async def test_google_search(self, query: str):
        """测试Google搜索"""
        print(f"\n🔍 测试Google搜索: '{query}'")
        try:
            start_time = time.time()
            results = await self.search_manager.search(
                query=query,
                num_results=5,
                engine=SearchEngine.GOOGLE
            )
            end_time = time.time()
            
            self.print_search_results(results, "Google")
            print(f"搜索耗时: {end_time - start_time:.2f}秒")
            return results
            
        except Exception as e:
            print(f"Google搜索失败: {e}")
            return []
    
    async def test_duckduckgo_search(self, query: str):
        """测试DuckDuckGo搜索"""
        print(f"\n🦆 测试DuckDuckGo搜索: '{query}'")
        try:
            start_time = time.time()
            results = await self.search_manager.search(
                query=query,
                num_results=5,
                engine=SearchEngine.DUCKDUCKGO
            )
            end_time = time.time()
            
            self.print_search_results(results, "DuckDuckGo")
            print(f"搜索耗时: {end_time - start_time:.2f}秒")
            return results
            
        except Exception as e:
            print(f"DuckDuckGo搜索失败: {e}")
            return []
    
    def test_traditional_requests(self, query: str):
        """测试传统requests方法"""
        print(f"\n📡 测试传统requests方法: '{query}'")
        start_time = time.time()
        result = self.traditional_search.search_with_requests(query)
        end_time = time.time()
        
        if result["success"]:
            print("--- 传统requests方法结果 ---")
            for i, item in enumerate(result["results"][:5], 1):
                print(f"{i}. 标题: {item['title']}")
                print(f"   链接: {item['url']}")
                print(f"   摘要: {item['snippet'][:100]}...")
                print()
        else:
            print(f"传统requests方法失败: {result['error']}")
        
        print(f"搜索耗时: {end_time - start_time:.2f}秒")
        return result
    
    async def test_multi_engine_search(self, query: str):
        """测试多引擎搜索"""
        print(f"\n🔄 测试多引擎搜索: '{query}'")
        try:
            start_time = time.time()
            results = await self.search_manager.multi_engine_search(
                query=query,
                num_results=3
            )
            end_time = time.time()
            
            print("--- 多引擎搜索结果 ---")
            for engine, engine_results in results.items():
                print(f"\n{engine.value.upper()} 引擎:")
                for i, result in enumerate(engine_results[:3], 1):
                    print(f"  {i}. {result.title}")
                    print(f"     {result.url}")
            
            print(f"\n多引擎搜索耗时: {end_time - start_time:.2f}秒")
            return results
            
        except Exception as e:
            print(f"多引擎搜索失败: {e}")
            return {}
    
    async def test_aggregate_search(self, query: str):
        """测试聚合搜索"""
        print(f"\n📊 测试聚合搜索: '{query}'")
        try:
            start_time = time.time()
            results = await self.search_manager.aggregate_search(
                query=query,
                num_results=5
            )
            end_time = time.time()
            
            self.print_search_results(results, "聚合搜索")
            print(f"聚合搜索耗时: {end_time - start_time:.2f}秒")
            return results
            
        except Exception as e:
            print(f"聚合搜索失败: {e}")
            return []
    
    def explain_differences(self):
        """解释搜索引擎与传统requests方法的区别"""
        print("\n" + "=" * 80)
        print("搜索引擎配置 vs 传统requests方法的区别")
        print("=" * 80)
        
        differences = [
            {
                "方面": "代码复用性",
                "搜索引擎配置": "统一接口，支持多种搜索引擎，易于切换",
                "传统requests": "每个搜索引擎需要单独实现，代码重复"
            },
            {
                "方面": "错误处理",
                "搜索引擎配置": "统一的异常处理和重试机制",
                "传统requests": "需要手动处理各种HTTP错误和超时"
            },
            {
                "方面": "异步支持",
                "搜索引擎配置": "原生支持异步操作，性能更好",
                "传统requests": "同步操作，需要额外工作支持异步"
            },
            {
                "方面": "配置管理",
                "搜索引擎配置": "集中配置管理，支持环境变量",
                "传统requests": "配置分散，难以管理"
            },
            {
                "方面": "结果标准化",
                "搜索引擎配置": "统一的SearchResult数据结构",
                "传统requests": "每个API返回格式不同，需要手动转换"
            },
            {
                "方面": "功能扩展",
                "搜索引擎配置": "支持多引擎搜索、结果聚合、评分等高级功能",
                "传统requests": "功能有限，扩展困难"
            },
            {
                "方面": "维护成本",
                "搜索引擎配置": "低维护成本，统一升级",
                "传统requests": "高维护成本，需要分别维护每个实现"
            }
        ]
        
        for diff in differences:
            print(f"\n📋 {diff['方面']}:")
            print(f"  ✅ 搜索引擎配置: {diff['搜索引擎配置']}")
            print(f"  ❌ 传统requests: {diff['传统requests']}")
        
        print("\n💡 总结:")
        print("搜索引擎配置提供了更高级的抽象层，使得搜索功能更加")
        print("可维护、可扩展和高性能。这对于需要集成多种搜索源的")
        print("应用程序（如RAG系统、知识检索等）特别有价值。")


async def main():
    """主测试函数"""
    print("🚀 搜索引擎测试开始")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化测试
    test = SearchEngineTest()
    
    # 打印配置信息
    test.print_config_info()
    
    # 测试查询
    test_queries = [
        "Python异步编程最佳实践",
        "人工智能在医疗领域的应用",
        "2024年科技趋势"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"测试查询: {query}")
        print(f"{'='*60}")
        
        # 测试Google搜索
        await test.test_google_search(query)
        
        # 测试DuckDuckGo搜索
        await test.test_duckduckgo_search(query)
        
        # 测试传统requests方法
        test.test_traditional_requests(query)
        
        # 测试多引擎搜索
        await test.test_multi_engine_search(query)
        
        # 测试聚合搜索
        await test.test_aggregate_search(query)
        
        print("\n" + "-" * 60)
        print("等待2秒后进行下一个测试...")
        await asyncio.sleep(2)
    
    # 解释区别
    test.explain_differences()
    
    print("\n✅ 搜索引擎测试完成")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()