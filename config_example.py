#!/usr/bin/env python3
"""配置使用示例

展示如何使用配置系统连接数据库和使用LLM服务
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (
    get_settings, 
    get_llm_config, 
    get_postgres_config, 
    get_redis_config
)

def main():
    """配置使用示例"""
    
    # 获取所有配置
    settings = get_settings()
    
    print("=" * 60)
    print("🔧 MindSearch 配置信息")
    print("=" * 60)
    
    # LLM配置示例
    llm_config = get_llm_config()
    print("\n🤖 LLM配置:")
    print(f"  默认提供商: {llm_config.default_provider}")
    print(f"  OpenAI模型: {llm_config.openai_model}")
    print(f"  硅基流动模型: {llm_config.siliconflow_model}")
    print(f"  硅基流动API密钥: {llm_config.siliconflow_api_key[:20] if llm_config.siliconflow_api_key else 'None'}...")
    print(f"  温度参数: {llm_config.temperature}")
    print(f"  最大令牌数: {llm_config.max_tokens}")
    
    # PostgreSQL配置示例
    postgres_config = get_postgres_config()
    print(f"\n🐘 PostgreSQL配置:")
    print(f"  主机: {postgres_config.host}")
    print(f"  端口: {postgres_config.port}")
    print(f"  数据库: {postgres_config.db}")
    print(f"  用户: {postgres_config.user}")
    print(f"  连接池大小: {postgres_config.pool_size}")
    print(f"  数据库URL: {postgres_config.database_url}")
    
    # Redis配置示例
    redis_config = get_redis_config()
    print(f"\n🔴 Redis配置:")
    print(f"  主机: {redis_config.host}")
    print(f"  端口: {redis_config.port}")
    print(f"  数据库: {redis_config.db}")
    print(f"  最大连接数: {redis_config.max_connections}")
    print(f"  缓存TTL: {redis_config.cache_ttl}秒")
    print(f"  Redis URL: {redis_config.redis_url}")
    
    # 服务器配置示例
    print(f"\n🌐 服务器配置:")
    print(f"  主机: {settings.server.host}")
    print(f"  端口: {settings.server.port}")
    print(f"  调试模式: {settings.server.debug}")
    print(f"  日志级别: {settings.server.log_level}")
    
    # 智能体配置示例
    print(f"\n🤖 智能体配置:")
    print(f"  最大子问题数: {settings.agent.max_sub_questions}")
    print(f"  最大迭代次数: {settings.agent.max_iterations}")
    print(f"  启用流式响应: {settings.agent.enable_streaming}")
    print(f"  智能体超时: {settings.agent.agent_timeout}秒")
    
    print("\n" + "=" * 60)
    print("✅ 配置加载完成！")
    print("=" * 60)


def demo_database_connection():
    """演示数据库连接配置使用"""
    postgres_config = get_postgres_config()
    redis_config = get_redis_config()
    
    print("\n📊 数据库连接示例:")
    print("\n# PostgreSQL连接示例 (使用SQLAlchemy):")
    print(f"from sqlalchemy import create_engine")
    print(f"engine = create_engine('{postgres_config.database_url}')")
    
    print("\n# Redis连接示例 (使用redis-py):")
    print(f"import redis")
    print(f"redis_client = redis.from_url('{redis_config.redis_url}')")
    
    print("\n# 或者使用单独的参数:")
    print(f"redis_client = redis.Redis(")
    print(f"    host='{redis_config.host}',")
    print(f"    port={redis_config.port},")
    print(f"    db={redis_config.db},")
    if redis_config.password:
        print(f"    password='{redis_config.password}',")
    print(f"    max_connections={redis_config.max_connections}")
    print(f")")


def demo_llm_usage():
    """演示LLM配置使用"""
    llm_config = get_llm_config()
    
    print("\n🤖 LLM使用示例:")
    
    if llm_config.default_provider == "siliconflow":
        print("\n# 使用硅基流动API:")
        print(f"from langchain_openai import ChatOpenAI")
        print(f"")
        print(f"llm = ChatOpenAI(")
        print(f"    api_key='{llm_config.siliconflow_api_key}',")
        print(f"    base_url='{llm_config.siliconflow_base_url}',")
        print(f"    model='{llm_config.siliconflow_model}',")
        print(f"    temperature={llm_config.temperature}")
        print(f")")
        print(f"")
        print(f"# 发送消息")
        print(f"response = llm.invoke('你好，请介绍一下你自己')")
        print(f"print(response.content)")
    
    elif llm_config.default_provider == "openai":
        print("\n# 使用OpenAI API:")
        print(f"from langchain_openai import ChatOpenAI")
        print(f"")
        print(f"llm = ChatOpenAI(")
        print(f"    api_key='{llm_config.openai_api_key}',")
        print(f"    model='{llm_config.openai_model}',")
        print(f"    temperature={llm_config.temperature}")
        print(f")")


if __name__ == "__main__":
    main()
    demo_database_connection()
    demo_llm_usage()