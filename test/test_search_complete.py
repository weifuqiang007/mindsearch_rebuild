#!/usr/bin/env python3
"""完整的搜索工具测试脚本

测试所有可用的搜索引擎功能
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.search_tools import get_search_manager, SearchEngine


async def test_search_engines():
    """测试所有可用的搜索引擎"""
    print("=== 搜索工具测试 ===")
    
    search_tool = get_search_manager()
    available_engines = search_tool.list_engines()
    
    print(f"可用的搜索引擎: {[engine.value for engine in available_engines]}")
    
    test_query = "2022年诺贝尔物理学奖获得者"
    print(f"测试查询: {test_query}")
    print("=" * 50)
    
    # 测试每个可用的搜索引擎
    for engine in available_engines:
        print(f"\n🔍 测试 {engine.value.upper()} 搜索引擎...")
        try:
            results = await search_tool.search(
                query=test_query,
                num_results=3,
                engine=engine
            )
            
            if results:
                print(f"✅ 成功找到 {len(results)} 个结果:")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. 标题: {result.title}")
                    print(f"   URL: {result.url}")
                    print(f"   摘要: {result.snippet[:150]}...")
                    print(f"   来源: {result.source}")
                    print(f"   评分: {result.score:.2f}")
            else:
                print("⚠️  没有找到结果")
                
        except Exception as e:
            print(f"❌ 搜索失败: {str(e)}")
        
        print("-" * 40)
    
    # 测试多引擎聚合搜索
    print("\n🔄 测试多引擎聚合搜索...")
    try:
        aggregated_results = await search_tool.aggregate_search(
            query=test_query,
            num_results=5
        )
        
        if aggregated_results:
            print(f"✅ 聚合搜索成功，共找到 {len(aggregated_results)} 个去重结果:")
            for i, result in enumerate(aggregated_results, 1):
                print(f"\n{i}. {result.title}")
                print(f"   来源: {result.source}")
                print(f"   评分: {result.score:.2f}")
        else:
            print("⚠️  聚合搜索没有找到结果")
            
    except Exception as e:
        print(f"❌ 聚合搜索失败: {str(e)}")


async def test_search_configuration():
    """测试搜索配置"""
    print("\n=== 搜索配置测试 ===")
    
    from config import get_search_config
    
    config = get_search_config()
    
    print(f"默认搜索引擎: {config.default_engine}")
    print(f"最大搜索结果数: {config.max_search_results}")
    print(f"搜索超时时间: {config.search_timeout}秒")
    print(f"最大内容长度: {config.max_content_length}")
    print(f"启用内容提取: {config.enable_content_extraction}")
    
    # 检查API密钥配置状态
    print("\nAPI密钥配置状态:")
    print(f"  Bing API Key: {'✅ 已配置' if config.bing_api_key else '❌ 未配置'}")
    print(f"  Google API Key: {'✅ 已配置' if config.google_api_key else '❌ 未配置'}")
    print(f"  Google CSE ID: {'✅ 已配置' if config.google_cse_id else '❌ 未配置'}")
    print(f"  Serper API Key: {'✅ 已配置' if config.serper_api_key else '❌ 未配置'}")


async def main():
    """主函数"""
    try:
        await test_search_configuration()
        await test_search_engines()
        
        print("\n=== 测试完成 ===")
        print("\n💡 使用建议:")
        print("1. DuckDuckGo: 免费，无需API密钥，但可能有网络限制")
        print("2. Google: 需要API密钥和自定义搜索引擎ID，结果质量高")
        print("3. Bing: 需要API密钥，结果质量好")
        print("4. Serper: 需要API密钥，基于Google搜索")
        print("5. 建议配置多个搜索引擎作为备选")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())