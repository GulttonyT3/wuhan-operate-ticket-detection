#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI抽取器对倒母操作的识别能力
"""

from ai_extractor import AIOperationTicketExtractor
import json

def test_daoma_operations():
    """测试倒母操作样本"""
    print("🔄 倒母操作识别测试")
    print("="*80)
    
    # 创建AI抽取器
    extractor = AIOperationTicketExtractor()
    
    # 测试连接
    if not extractor.test_connection():
        print("❌ API连接失败")
        return
    
    print("✅ API连接成功\n")
    
    # 倒母操作测试样本（从真实数据中提取）
    test_cases = [
        {
            "text": "新舵落口站舵#2主变220kV侧舵211开关由舵#3母线倒至舵#4母线运行",
            "expected": {
                "初始状态": "舵#3母线",
                "目标状态": "舵#4母线运行", 
                "操作": "倒母操作",
                "操作设备": "舵#2主变220kV侧舵211开关",
                "设备所属厂站": "新舵落口站",
                "设备所属线路": ""
            }
        },
        {
            "text": "巡司河站220kV巡#1主变220kV侧巡06开关由巡#2母线倒至巡#1母线运行",
            "expected": {
                "初始状态": "巡#2母线",
                "目标状态": "巡#1母线运行",
                "操作": "倒母操作", 
                "操作设备": "220kV巡#1主变220kV侧巡06开关",
                "设备所属厂站": "巡司河站",
                "设备所属线路": ""
            }
        },
        {
            "text": "宗关站220kV舵宗一回宗223开关由220kV宗#2母线倒至220kV宗#1母线运行",
            "expected": {
                "初始状态": "220kV宗#2母线",
                "目标状态": "220kV宗#1母线运行",
                "操作": "倒母操作",
                "操作设备": "宗223开关", 
                "设备所属厂站": "宗关站",
                "设备所属线路": "220kV舵宗一回"
            }
        },
        {
            "text": "生物园站220kV物#2主变220kV侧物209开关由220kV物#2母线停电倒至物220kV物#1母线热备用",
            "expected": {
                "初始状态": "220kV物#2母线停电",
                "目标状态": "物220kV物#1母线热备用",
                "操作": "倒母操作",
                "操作设备": "220kV物#2主变220kV侧物209开关",
                "设备所属厂站": "生物园站", 
                "设备所属线路": ""
            }
        }
    ]
    
    # 测试结果统计
    total_tests = len(test_cases)
    correct_operations = 0
    field_stats = {
        "初始状态": 0,
        "目标状态": 0,
        "操作": 0,
        "操作设备": 0,
        "设备所属厂站": 0,
        "设备所属线路": 0
    }
    
    for i, case in enumerate(test_cases, 1):
        print(f"📝 测试样本 {i}:")
        print(f"原始文本: {case['text']}")
        print()
        
        try:
            # AI抽取
            ai_result = extractor.extract_single_text(case['text'])
            
            print("🤖 AI抽取结果:")
            for key, value in ai_result.items():
                print(f"  {key}: {value}")
            
            print("\n📋 期望结果:")
            for key, value in case['expected'].items():
                print(f"  {key}: {value}")
            
            print("\n🔍 对比分析:")
            
            # 字段级别对比
            field_correct = 0
            for field in field_stats.keys():
                ai_value = str(ai_result.get(field, "")).strip()
                expected_value = str(case['expected'].get(field, "")).strip()
                
                # 处理None值
                if expected_value == "None":
                    expected_value = ""
                
                is_correct = ai_value == expected_value
                if is_correct:
                    field_stats[field] += 1
                    field_correct += 1
                
                status = "✅" if is_correct else "❌"
                print(f"  {status} {field}: AI='{ai_value}' vs 期望='{expected_value}'")
            
            accuracy = field_correct / len(field_stats)
            print(f"\n📊 样本准确率: {accuracy:.1%} ({field_correct}/{len(field_stats)})")
            
            # 特别关注操作类型识别
            if ai_result.get('操作') == '倒母操作':
                correct_operations += 1
                print("🎯 倒母操作识别: ✅ 正确")
            else:
                print(f"🎯 倒母操作识别: ❌ 错误 (识别为: {ai_result.get('操作')})")
            
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ 抽取失败: {e}")
            print("=" * 80)
    
    # 总体统计
    print("\n📊 倒母操作测试总结:")
    print("=" * 50)
    
    print(f"倒母操作识别准确率: {correct_operations}/{total_tests} = {correct_operations/total_tests:.1%}")
    
    print("\n各字段准确率:")
    for field, correct_count in field_stats.items():
        accuracy = correct_count / total_tests
        print(f"  {field}: {correct_count}/{total_tests} = {accuracy:.1%}")
    
    overall_accuracy = sum(field_stats.values()) / (total_tests * len(field_stats))
    print(f"\n总体准确率: {overall_accuracy:.1%}")
    
    # 倒母操作特征分析
    print("\n🔍 倒母操作特征分析:")
    print("-" * 30)
    print("典型模式:")
    print("1. 文本包含 '倒至' 关键词")
    print("2. 初始状态和目标状态都包含 '母线'")
    print("3. 通常是220kV等级的主变操作")
    print("4. 涉及不同母线间的切换")
    
    return {
        'operation_accuracy': correct_operations / total_tests,
        'field_accuracies': {k: v/total_tests for k, v in field_stats.items()},
        'overall_accuracy': overall_accuracy
    }

if __name__ == "__main__":
    results = test_daoma_operations()
    
    print(f"\n🎉 测试完成!")
    print(f"倒母操作识别能力: {'优秀' if results['operation_accuracy'] >= 0.8 else '需要改进'}")
