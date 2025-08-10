import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.search_tools import get_search_manager, SearchEngine
import asyncio

async def test_search():
    search_tool = get_search_manager()
    
    print("可用的搜索引擎:", search_tool.list_engines())
    
    # 测试DuckDuckGo搜索（免费，不需要API key）
    try:
        print("\n测试DuckDuckGo搜索...")
        results = await search_tool.search(
            query="2022年诺贝尔物理学奖获得者?", 
            num_results=3, 
            engine=SearchEngine.DUCKDUCKGO
        )
        
        print(f"找到 {len(results)} 个结果:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   摘要: {result.snippet[:100]}...")
            print()
            
    except Exception as e:
        print(f"搜索失败: {e}")
    
    # 如果有Google API配置，测试Google搜索
    try:
        if SearchEngine.GOOGLE in search_tool.list_engines():
            print("\n测试Google搜索...")
            google_results = await search_tool.search(
                query="2022年诺贝尔物理学奖获得者?", 
                num_results=3, 
                engine=SearchEngine.GOOGLE
            )
            print(f"Google搜索找到 {len(google_results)} 个结果")
        else:
            print("\nGoogle搜索未配置API key")
    except Exception as e:
        print(f"Google搜索失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_search())