#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI抽取器接口测试脚本
提供简单的命令行接口测试AI抽取功能
"""

import json
import sys
from ai_extractor import AIOperationTicketExtractor

def test_single_text():
    """测试单个文本抽取"""
    print("="*60)
    print("单个文本抽取测试")
    print("="*60)
    
    # 创建抽取器
    extractor = AIOperationTicketExtractor()
    
    # 测试连接
    print("🔗 测试API连接...")
    if not extractor.test_connection():
        print("❌ API连接失败，请检查网络和API服务")
        return False
    
    print("✅ API连接成功")
    print()
    
    # 测试样本
    test_cases = [
        "10kV展路灯线前一路灯环网箱变04开关由热备用转运行",
        "山坡站35kV乌山安土线由检修转冷备用",
        "10kV东开线万科汉口传奇开闭所09开关至末端段线路由检修转冷备用（万科汉口传奇开闭所09开关冷备用）"
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"📝 测试样本 {i}:")
        print(f"输入: {text}")
        print("🤖 AI抽取结果:")
        
        try:
            result = extractor.extract_single_text(text)
            
            # 格式化输出
            for key, value in result.items():
                status = "✅" if value else "⚪"
                print(f"  {status} {key}: {value}")
            
            print()
            
        except Exception as e:
            print(f"❌ 抽取失败: {e}")
            print()
    
    return True

def test_batch_processing():
    """测试批量处理"""
    print("="*60)
    print("批量处理测试")
    print("="*60)
    
    extractor = AIOperationTicketExtractor()
    
    # 批量测试文本
    texts = [
        "10kV展路灯线前一路灯环网箱变04开关由热备用转运行",
        "山坡站35kV乌山安土线由检修转冷备用",
        "姚家山站姚#3主变10kV姚68开关由热备用转运行"
    ]
    
    print(f"📦 批量处理 {len(texts)} 条文本...")
    
    try:
        results = extractor.extract_batch(texts, batch_delay=0.5)
        
        print("✅ 批量处理完成")
        print("\n📊 JSON格式结果:")
        print(json.dumps(results, ensure_ascii=False, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ 批量处理失败: {e}")
        return False

def interactive_test():
    """交互式测试"""
    print("="*60)
    print("交互式测试 (输入 'quit' 退出)")
    print("="*60)
    
    extractor = AIOperationTicketExtractor()
    
    # 测试连接
    if not extractor.test_connection():
        print("❌ API连接失败")
        return
    
    print("✅ API连接成功，请输入操作票文本进行测试")
    print()
    
    while True:
        try:
            # 获取用户输入
            text = input("📝 请输入操作票文本 (或 'quit' 退出): ").strip()
            
            if text.lower() in ['quit', 'exit', 'q']:
                print("👋 退出测试")
                break
            
            if not text:
                print("⚠️ 请输入有效的文本")
                continue
            
            print(f"\n🤖 正在分析: {text}")
            print("-" * 40)
            
            # 抽取信息
            result = extractor.extract_single_text(text)
            
            # 输出结果
            print("📋 抽取结果:")
            for key, value in result.items():
                status = "✅" if value else "⚪"
                print(f"  {status} {key}: {value}")
            
            # JSON格式
            print(f"\n💾 JSON格式:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print()
            
        except KeyboardInterrupt:
            print("\n👋 用户中断，退出测试")
            break
        except Exception as e:
            print(f"❌ 处理错误: {e}")
            print()

def performance_test():
    """性能测试"""
    print("="*60)
    print("性能测试")
    print("="*60)
    
    extractor = AIOperationTicketExtractor()
    
    if not extractor.test_connection():
        print("❌ API连接失败")
        return
    
    # 性能测试样本
    test_text = "10kV展路灯线前一路灯环网箱变04开关由热备用转运行"
    test_count = 5
    
    print(f"⏱️ 性能测试: 连续处理 {test_count} 次相同文本")
    print(f"测试文本: {test_text}")
    print()
    
    import time
    
    times = []
    
    for i in range(test_count):
        print(f"🔄 第 {i+1}/{test_count} 次测试...")
        
        start_time = time.time()
        try:
            result = extractor.extract_single_text(test_text)
            end_time = time.time()
            
            duration = end_time - start_time
            times.append(duration)
            
            print(f"  ✅ 耗时: {duration:.2f}秒")
            
        except Exception as e:
            print(f"  ❌ 失败: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📊 性能统计:")
        print(f"  平均耗时: {avg_time:.2f}秒")
        print(f"  最快: {min_time:.2f}秒")
        print(f"  最慢: {max_time:.2f}秒")
        print(f"  成功率: {len(times)}/{test_count} ({len(times)/test_count*100:.1f}%)")

def main():
    """主函数"""
    print("🚀 AI操作票信息抽取器 - 接口测试")
    print("="*60)
    print("API配置:")
    print("  地址: http://192.168.64.19:21018")
    print("  模型: sh-ticket-analyse-model-fastchat—1")
    print("="*60)
    
    if len(sys.argv) > 1:
        # 命令行参数模式
        mode = sys.argv[1].lower()
        
        if mode == "single":
            test_single_text()
        elif mode == "batch":
            test_batch_processing()
        elif mode == "interactive":
            interactive_test()
        elif mode == "performance":
            performance_test()
        else:
            print(f"❌ 未知模式: {mode}")
            print("可用模式: single, batch, interactive, performance")
    else:
        # 交互式选择模式
        print("\n请选择测试模式:")
        print("1. 单个文本测试 (预设样本)")
        print("2. 批量处理测试")
        print("3. 交互式测试 (手动输入)")
        print("4. 性能测试")
        print("5. 全部测试")
        
        try:
            choice = input("\n请输入选项 (1-5): ").strip()
            
            if choice == "1":
                test_single_text()
            elif choice == "2":
                test_batch_processing()
            elif choice == "3":
                interactive_test()
            elif choice == "4":
                performance_test()
            elif choice == "5":
                print("🔄 运行全部测试...\n")
                test_single_text()
                print()
                test_batch_processing()
                print()
                performance_test()
            else:
                print("❌ 无效选项")
                
        except KeyboardInterrupt:
            print("\n👋 用户取消")

if __name__ == "__main__":
    main()
