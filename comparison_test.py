#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI抽取器 vs 规则抽取器对比测试
"""

import json
import time
from ai_extractor import AIOperationTicketExtractor
from final_extractor import FinalOperationTicketExtractor

def compare_extractors():
    """对比两种抽取器的效果"""
    print("AI抽取器 vs 规则抽取器对比测试")
    print("="*80)
    
    # 创建两个抽取器
    ai_extractor = AIOperationTicketExtractor()
    rule_extractor = FinalOperationTicketExtractor()
    
    # 测试AI连接
    if not ai_extractor.test_connection():
        print("❌ AI抽取器连接失败")
        return
    
    print("✅ AI抽取器连接成功")
    print()
    
    # 测试样本
    test_cases = [
        {
            "name": "基础状态转换",
            "text": "10kV展路灯线前一路灯环网箱变04开关由热备用转运行",
            "expected": {
                "初始状态": "热备用",
                "目标状态": "运行", 
                "操作": "状态转换",
                "操作设备": "前一路灯环网箱变04开关",
                "设备所属厂站": "",
                "设备所属线路": "10kV展路灯线"
            }
        },
        {
            "name": "带厂站信息",
            "text": "山坡站35kV乌山安土线由检修转冷备用",
            "expected": {
                "初始状态": "检修",
                "目标状态": "冷备用",
                "操作": "状态转换", 
                "操作设备": "35kV乌山安土线",
                "设备所属厂站": "山坡站",
                "设备所属线路": ""
            }
        },
        {
            "name": "复杂设备名称",
            "text": "10kV东开线万科汉口传奇开闭所09开关至末端段线路由检修转冷备用（万科汉口传奇开闭所09开关冷备用）",
            "expected": {
                "初始状态": "检修",
                "目标状态": "冷备用",
                "操作": "状态转换",
                "操作设备": "万科汉口传奇开闭所09开关",
                "设备所属厂站": "",
                "设备所属线路": "10kV东开线"
            }
        },
        {
            "name": "带变电站信息",
            "text": "姚家山站姚#3主变10kV姚68开关由热备用转运行",
            "expected": {
                "初始状态": "热备用",
                "目标状态": "运行",
                "操作": "状态转换",
                "操作设备": "姚#3主变10kV姚68开关",
                "设备所属厂站": "姚家山站",
                "设备所属线路": ""
            }
        },
        {
            "name": "环网柜操作",
            "text": "10kV佳海二回#3环网柜05开关由热备用转冷备用",
            "expected": {
                "初始状态": "热备用",
                "目标状态": "冷备用",
                "操作": "状态转换",
                "操作设备": "#3环网柜05开关",
                "设备所属厂站": "",
                "设备所属线路": "10kV佳海二回"
            }
        }
    ]
    
    # 对比结果
    comparison_results = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {case['name']}")
        print(f"文本: {case['text']}")
        print("-" * 60)
        
        # 规则抽取
        print("规则抽取结果:")
        rule_result = rule_extractor.extract_single_text(case['text'])
        for key, value in rule_result.items():
            print(f"  {key}: {value}")
        
        # AI抽取
        print("\nAI抽取结果:")
        ai_result = ai_extractor.extract_single_text(case['text'])
        for key, value in ai_result.items():
            print(f"  {key}: {value}")
        
        # 期望结果
        print("\n期望结果:")
        for key, value in case['expected'].items():
            print(f"  {key}: {value}")
        
        # 计算准确率
        rule_accuracy = calculate_accuracy(rule_result, case['expected'])
        ai_accuracy = calculate_accuracy(ai_result, case['expected'])
        
        print(f"\n准确率对比:")
        print(f"  规则抽取: {rule_accuracy:.1%} ({rule_accuracy*6:.0f}/6)")
        print(f"  AI抽取:   {ai_accuracy:.1%} ({ai_accuracy*6:.0f}/6)")
        
        if ai_accuracy > rule_accuracy:
            print("  🏆 AI抽取器胜出")
        elif rule_accuracy > ai_accuracy:
            print("  🏆 规则抽取器胜出")
        else:
            print("  🤝 平局")
        
        comparison_results.append({
            'case_name': case['name'],
            'text': case['text'],
            'rule_result': rule_result,
            'ai_result': ai_result,
            'expected': case['expected'],
            'rule_accuracy': rule_accuracy,
            'ai_accuracy': ai_accuracy
        })
        
        print("=" * 80)
        
        # 添加延迟避免API限流
        if i < len(test_cases):
            time.sleep(0.5)
    
    # 总体统计
    print("\n总体统计:")
    print("=" * 40)
    
    total_rule_accuracy = sum(r['rule_accuracy'] for r in comparison_results) / len(comparison_results)
    total_ai_accuracy = sum(r['ai_accuracy'] for r in comparison_results) / len(comparison_results)
    
    print(f"规则抽取器平均准确率: {total_rule_accuracy:.1%}")
    print(f"AI抽取器平均准确率:   {total_ai_accuracy:.1%}")
    
    ai_wins = sum(1 for r in comparison_results if r['ai_accuracy'] > r['rule_accuracy'])
    rule_wins = sum(1 for r in comparison_results if r['rule_accuracy'] > r['ai_accuracy'])
    ties = len(comparison_results) - ai_wins - rule_wins
    
    print(f"\n胜负统计:")
    print(f"AI抽取器获胜: {ai_wins} 次")
    print(f"规则抽取器获胜: {rule_wins} 次")
    print(f"平局: {ties} 次")
    
    if total_ai_accuracy > total_rule_accuracy:
        print(f"\n🎉 AI抽取器整体表现更佳，准确率提升 {(total_ai_accuracy - total_rule_accuracy)*100:.1f}%")
    elif total_rule_accuracy > total_ai_accuracy:
        print(f"\n📊 规则抽取器整体表现更佳，准确率高出 {(total_rule_accuracy - total_ai_accuracy)*100:.1f}%")
    else:
        print(f"\n⚖️ 两种方法整体表现相当")
    
    return comparison_results

def calculate_accuracy(result: dict, expected: dict) -> float:
    """计算单个样本的准确率"""
    correct = 0
    total = len(expected)
    
    for key, expected_value in expected.items():
        actual_value = result.get(key, "")
        
        # 处理None值
        if expected_value is None:
            expected_value = ""
        if actual_value is None:
            actual_value = ""
        
        if str(expected_value).strip() == str(actual_value).strip():
            correct += 1
    
    return correct / total if total > 0 else 0

def field_wise_comparison():
    """按字段进行详细对比"""
    print("\n按字段详细对比")
    print("="*80)
    
    ai_extractor = AIOperationTicketExtractor()
    rule_extractor = FinalOperationTicketExtractor()
    
    # 从标注数据中随机选择一些样本进行测试
    try:
        with open('/Users/zzh/Downloads/武汉操作票抽取/cczl_annotation_data.json', 'r', encoding='utf-8') as f:
            annotation_data = json.load(f)
        
        # 选择前10个样本进行详细对比
        test_samples = annotation_data[:10]
        
        field_stats = {
            "初始状态": {"rule_correct": 0, "ai_correct": 0},
            "目标状态": {"rule_correct": 0, "ai_correct": 0},
            "操作": {"rule_correct": 0, "ai_correct": 0},
            "操作设备": {"rule_correct": 0, "ai_correct": 0},
            "设备所属厂站": {"rule_correct": 0, "ai_correct": 0},
            "设备所属线路": {"rule_correct": 0, "ai_correct": 0}
        }
        
        print(f"使用 {len(test_samples)} 个真实标注样本进行测试...")
        
        for i, sample in enumerate(test_samples):
            text = sample['原始文本']
            expected = sample['标注结果']
            
            # 规则抽取
            rule_result = rule_extractor.extract_single_text(text)
            
            # AI抽取 (添加延迟)
            ai_result = ai_extractor.extract_single_text(text)
            time.sleep(0.5)
            
            # 统计各字段准确率
            for field in field_stats.keys():
                expected_value = expected.get(field, "")
                rule_value = rule_result.get(field, "")
                ai_value = ai_result.get(field, "")
                
                # 处理None值
                if expected_value is None:
                    expected_value = ""
                if rule_value is None:
                    rule_value = ""
                if ai_value is None:
                    ai_value = ""
                
                if str(expected_value).strip() == str(rule_value).strip():
                    field_stats[field]["rule_correct"] += 1
                
                if str(expected_value).strip() == str(ai_value).strip():
                    field_stats[field]["ai_correct"] += 1
            
            print(f"完成样本 {i+1}/{len(test_samples)}")
        
        # 输出字段级别的对比结果
        print(f"\n字段级别准确率对比 (基于{len(test_samples)}个样本):")
        print("-" * 60)
        print(f"{'字段':<12} {'规则方法':<12} {'AI方法':<12} {'提升':<10}")
        print("-" * 60)
        
        for field, stats in field_stats.items():
            rule_acc = stats["rule_correct"] / len(test_samples)
            ai_acc = stats["ai_correct"] / len(test_samples)
            improvement = ai_acc - rule_acc
            
            improvement_str = f"+{improvement:.1%}" if improvement > 0 else f"{improvement:.1%}"
            print(f"{field:<12} {rule_acc:<12.1%} {ai_acc:<12.1%} {improvement_str:<10}")
        
        # 总体对比
        total_rule_correct = sum(stats["rule_correct"] for stats in field_stats.values())
        total_ai_correct = sum(stats["ai_correct"] for stats in field_stats.values())
        total_possible = len(test_samples) * len(field_stats)
        
        total_rule_acc = total_rule_correct / total_possible
        total_ai_acc = total_ai_correct / total_possible
        total_improvement = total_ai_acc - total_rule_acc
        
        print("-" * 60)
        print(f"{'总体':<12} {total_rule_acc:<12.1%} {total_ai_acc:<12.1%} {total_improvement:+.1%}")
        
    except Exception as e:
        print(f"字段级对比测试失败: {e}")

if __name__ == "__main__":
    # 基础对比测试
    comparison_results = compare_extractors()
    
    # 字段级详细对比
    field_wise_comparison()
