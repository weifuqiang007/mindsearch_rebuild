#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试graph_search_example.py的输出保存功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入graph_search_example模块
try:
    from examples.graph_search_example import (
        log_output, 
        print_callback, 
        print_graph_statistics,
        save_output_to_markdown,
        output_buffer
    )
except ImportError:
    # 如果直接导入失败，尝试添加examples目录到路径
    examples_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '')
    sys.path.append(examples_path)
    from graph_search_example import (
        log_output, 
        print_callback, 
        print_graph_statistics,
        save_output_to_markdown,
        output_buffer
    )

def test_output_logging():
    """测试输出记录功能"""
    print("🧪 测试输出记录功能...")
    
    # 清空输出缓冲区
    output_buffer.clear()
    
    # 测试基本输出
    log_output("=== 测试开始 ===")
    log_output("🔍 这是一个测试查询")
    log_output("📊 测试统计信息:")
    log_output("  总节点数: 5")
    log_output("  成功节点: 3")
    log_output("  失败节点: 2")
    
    # 测试回调函数
    print_callback("搜索进度更新", step=1, total=5, status="running")
    print_callback("节点执行完成", node_id="search_0", result="success")
    
    # 测试统计信息打印
    mock_stats = {
        'graph_stats': {
            'total_nodes': 5,
            'completed_nodes': 3,
            'failed_nodes': 2,
            'success_rate': 0.6,
            'execution_time': 15.5,
            'node_details': {
                'search_0': {'status': 'completed', 'error': None},
                'search_1': {'status': 'completed', 'error': None},
                'search_2': {'status': 'failed', 'error': 'SSL connection error'},
                'search_3': {'status': 'completed', 'error': None},
                'search_4': {'status': 'failed', 'error': 'Timeout'}
            }
        }
    }
    
    print_graph_statistics(mock_stats)
    
    log_output("\n🎉 测试完成！")
    log_output("\n💡 这是一个完整的测试输出示例。")
    
    print(f"\n📊 输出缓冲区包含 {len(output_buffer)} 行内容")
    
    # 保存到markdown文件
    filename = save_output_to_markdown()
    
    print(f"\n✅ 测试完成！输出已保存到: {filename}")
    return filename

def verify_markdown_file(filename):
    """验证生成的markdown文件"""
    print(f"\n🔍 验证markdown文件: {filename}")
    
    if not os.path.exists(filename):
        print(f"❌ 文件不存在: {filename}")
        return False
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查文件内容
    checks = [
        ("# MindSearchAgent" in content, "标题检查"),
        ("执行时间" in content, "时间戳检查"),
        ("测试开始" in content, "测试内容检查"),
        ("图执行统计" in content, "统计信息检查"),
        ("SSL connection error" in content, "错误信息检查"),
        ("测试完成" in content, "完成标记检查")
    ]
    
    all_passed = True
    for check, description in checks:
        if check:
            print(f"  ✅ {description}: 通过")
        else:
            print(f"  ❌ {description}: 失败")
            all_passed = False
    
    print(f"\n📄 文件大小: {len(content)} 字符")
    print(f"📄 文件行数: {len(content.splitlines())} 行")
    
    if all_passed:
        print("\n🎉 所有检查都通过了！")
    else:
        print("\n⚠️ 部分检查失败，请检查文件内容。")
    
    return all_passed

def main():
    """主测试函数"""
    print("🚀 开始测试graph_search_example.py的输出保存功能")
    print("="*60)
    
    try:
        # 运行测试
        filename = test_output_logging()
        
        # 验证文件
        success = verify_markdown_file(filename)
        
        if success:
            print("\n🎯 测试结果: 成功！")
            print(f"📁 生成的文件: {filename}")
            print("\n💡 现在您可以运行graph_search_example.py，所有输出都会保存到markdown文件中。")
        else:
            print("\n❌ 测试结果: 失败！")
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()