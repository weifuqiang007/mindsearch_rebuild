#!/usr/bin/env python3
"""简单的启动脚本

直接运行服务器，避免复杂的导入问题
"""

import uvicorn
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """主函数"""
    # 设置默认环境变量
    os.environ.setdefault("ENVIRONMENT", "development")
    
    print("="*60)
    print("🚀 LangChain MindSearch 启动中...")
    print("="*60)
    print(f"环境: {os.environ.get('ENVIRONMENT', 'development')}")
    print(f"主机: localhost")
    print(f"端口: 8000")
    print(f"文档: http://localhost:8000/docs")
    print(f"WebSocket: ws://localhost:8000/ws/{{session_id}}")
    print("="*60)
    
    try:
        # 直接使用uvicorn启动
        uvicorn.run(
            "langchain_rebuild.api.server:create_app",
            factory=True,
            host="localhost",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()