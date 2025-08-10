#!/usr/bin/env python3
"""LangChain MindSearch 主启动文件

提供简单的启动入口
"""

import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.server import run_server
from config import get_server_config

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="LangChain MindSearch - 基于LangChain重构的智能搜索系统"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="服务器主机地址 (默认: 从配置文件读取)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="服务器端口 (默认: 从配置文件读取)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载 (开发模式)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="配置文件路径"
    )
    
    parser.add_argument(
        "--env",
        type=str,
        default="development",
        choices=["development", "production", "testing"],
        help="运行环境"
    )
    
    args = parser.parse_args()
    
    # 设置环境变量（如果需要）
    if args.config:
        os.environ["CONFIG_FILE"] = args.config
    
    # 直接传递环境参数获取配置，不再依赖环境变量
    config = get_server_config(environment=args.env)
    
    # 显示启动信息
    print("="*60)
    print("🚀 LangChain MindSearch 启动中...")
    print("="*60)
    print(f"环境: {args.env}")
    print(f"主机: {args.host or config.host}")
    print(f"端口: {args.port or config.port}")
    print(f"重载: {'是' if args.reload else '否'}")
    print(f"文档: http://{args.host or config.host}:{args.port or config.port}/docs")
    print("="*60)
    
    try:
        # 启动服务器
        run_server(
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()