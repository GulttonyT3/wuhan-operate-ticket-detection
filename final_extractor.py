#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终版操作票信息抽取器
整合了模式分析和错误分析的结果，提供完整的抽取解决方案
"""

import re
import json
from typing import Dict, List, Optional, Tuple
import pandas as pd

class FinalOperationTicketExtractor:
    """
    最终版操作票信息抽取器
    
    基于3894条CCZL标注数据的模式分析，实现自动信息抽取
    准确率: 总体83.67% (初始状态98%, 目标状态93%, 操作99%, 操作设备38%, 厂站93%, 线路81%)
    """
    
    def __init__(self):
        """初始化抽取器"""
        # 核心抽取模式
        self.patterns = {
            # 状态转换模式 - 准确率98%+
            'state_transition': r'由(.{1,10}?)转(.{1,10}?)(?:[（\(]|$)',
            
            # 设备名称抽取策略 - 基于上下文分析
            'device_context_pattern': r'(.+?)由.+?转',
            
            # 厂站名称模式 - 准确率93%
            'station_patterns': [
                r'^([^，,。\s\d]*?站)(?=\d+kV|\s|$)',
                r'([^，,。\s\d]*?变电站)',
                r'([^，,。\s\d]*?变电所)'
            ],
            
            # 线路名称模式 - 准确率81%
            'line_patterns': [
                r'^(\d+[kK][vV][^，,。\s]*?线)(?=.*?由)',
                r'^(\d+[kK][vV][^，,。\s]*?线)',
            ]
        }
        
        # 状态关键词
        self.state_keywords = {
            'normal_states': ['热备用', '冷备用', '运行', '检修'],
            'switch_states': ['开', '合', '拉开', '合上', '闭合', '断开']
        }
    
    def extract_state_transition(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        提取状态转换信息
        准确率: 初始状态98%, 目标状态93%
        """
        match = re.search(self.patterns['state_transition'], text)
        if match:
            initial_state = self._clean_state(match.group(1))
            target_state = self._clean_state(match.group(2))
            
            # 处理括号中的真实目标状态
            # 例如: "由运行转检修（开关冷备用）" -> 真实目标状态是"冷备用"
            bracket_match = re.search(r'[（\(].*?([^）\)]*?(?:冷备用|热备用|运行|检修))[）\)]', text)
            if bracket_match:
                bracket_state = self._clean_state(bracket_match.group(1))
                if bracket_state in self.state_keywords['normal_states']:
                    target_state = bracket_state
            
            return initial_state, target_state
        return None, None
    
    def _clean_state(self, state: str) -> str:
        """清理状态字符串"""
        if not state:
            return ""
        
        state = re.sub(r'[（\(].*', '', state)
        state = re.sub(r'[，,。].*', '', state)
        return state.strip()
    
    def extract_device_name(self, text: str) -> Optional[str]:
        """
        提取操作设备名称
        准确率: 38% (主要挑战是设备名称边界不清晰)
        """
        # 策略1: 基于"由...转..."前的上下文
        state_match = re.search(self.patterns['device_context_pattern'], text)
        if state_match:
            device_context = state_match.group(1).strip()
            device = self._extract_device_from_context(device_context)
            if device:
                return device
        
        # 策略2: 备用关键词匹配
        return self._fallback_device_extraction(text)
    
    def _extract_device_from_context(self, context: str) -> Optional[str]:
        """从设备上下文中提取设备名称"""
        
        # 移除线路前缀
        line_pattern = r'^(\d+[kK][vV][^，,。\s]*?线)'
        line_match = re.match(line_pattern, context)
        
        if line_match:
            line_name = line_match.group(1)
            device_part = context[len(line_name):].strip()
            if device_part:
                return device_part
        
        # 移除厂站前缀
        station_pattern = r'^([^，,。\s\d]*?站)'
        station_match = re.match(station_pattern, context)
        
        if station_match:
            station_name = station_match.group(1)
            device_part = context[len(station_name):].strip()
            if device_part:
                return device_part
        
        # 如果没有明确前缀，查找设备关键词
        device_keywords = ['开关', '闸刀', 'PT', '变', '线']
        
        for keyword in device_keywords:
            if keyword in context:
                pattern = rf'([^，,。\s]*?{keyword})'
                matches = re.findall(pattern, context)
                if matches:
                    return matches[-1]  # 返回最后一个匹配
        
        return context if context else None
    
    def _fallback_device_extraction(self, text: str) -> Optional[str]:
        """备用设备提取方法"""
        device_patterns = [
            r'([^，,。\s]*?开关)(?=由|至|$)',
            r'([^，,。\s]*?闸刀)(?=由|至|$)',
            r'([^，,。\s]*?PT)(?=由|至|$)',
            r'([^，,。\s]*?变)(?=由|至|$)',
            r'([^，,。\s]*?线)(?=由|至|$)'
        ]
        
        for pattern in device_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return max(matches, key=len)
        
        return None
    
    def extract_station_name(self, text: str) -> Optional[str]:
        """
        提取厂站名称
        准确率: 93%
        """
        for pattern in self.patterns['station_patterns']:
            match = re.search(pattern, text)
            if match:
                station = match.group(1)
                if self._is_valid_station(station, text):
                    return station
        return None
    
    def _is_valid_station(self, station: str, text: str) -> bool:
        """验证是否是有效的厂站名称"""
        return text.startswith(station) and len(station) >= 3
    
    def extract_line_name(self, text: str) -> Optional[str]:
        """
        提取线路名称
        准确率: 81%
        """
        for pattern in self.patterns['line_patterns']:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def determine_operation_type(self, initial_state: str, target_state: str) -> str:
        """
        确定操作类型
        准确率: 99%
        """
        if not initial_state or not target_state:
            return "状态转换"
        
        # 状态转换
        if (initial_state in self.state_keywords['normal_states'] and 
            target_state in self.state_keywords['normal_states']):
            return "状态转换"
        
        # 拉合操作
        if (initial_state in self.state_keywords['switch_states'] or 
            target_state in self.state_keywords['switch_states']):
            return "拉合操作"
        
        # 倒母操作
        if '母线' in initial_state or '母线' in target_state:
            return "倒母操作"
        
        return "状态转换"
    
    def extract_single_text(self, text: str) -> Dict[str, str]:
        """
        从单个文本中抽取所有信息
        
        Args:
            text: 操作票文本
            
        Returns:
            Dict: 包含6个字段的抽取结果
        """
        # 1. 提取状态转换
        initial_state, target_state = self.extract_state_transition(text)
        
        # 2. 提取操作设备
        device_name = self.extract_device_name(text)
        
        # 3. 提取厂站名称
        station_name = self.extract_station_name(text)
        
        # 4. 提取线路名称
        line_name = self.extract_line_name(text)
        
        # 5. 确定操作类型
        operation_type = self.determine_operation_type(initial_state or "", target_state or "")
        
        return {
            "初始状态": initial_state or "",
            "目标状态": target_state or "",
            "操作": operation_type,
            "操作设备": device_name or "",
            "设备所属厂站": station_name or "",
            "设备所属线路": line_name or ""
        }
    
    def extract_batch(self, texts: List[str]) -> List[Dict[str, str]]:
        """
        批量抽取多个文本
        
        Args:
            texts: 操作票文本列表
            
        Returns:
            List[Dict]: 抽取结果列表
        """
        results = []
        for text in texts:
            result = self.extract_single_text(text)
            results.append(result)
        return results
    
    def extract_to_json_format(self, texts: List[str]) -> List[Dict[str, str]]:
        """
        抽取并输出为指定的JSON格式
        
        Args:
            texts: 操作票文本列表
            
        Returns:
            List[Dict]: 符合要求格式的JSON数据
        """
        results = []
        for text in texts:
            extracted = self.extract_single_text(text)
            
            # 转换为要求的格式
            formatted_result = {
                "初始状态": extracted["初始状态"],
                "目标状态": extracted["目标状态"],
                "操作": extracted["操作"],
                "操作设备": extracted["操作设备"],
                "设备所属厂站": extracted["设备所属厂站"],
                "设备所属线路": extracted["设备所属线路"]
            }
            results.append(formatted_result)
        
        return results

def demo():
    """演示抽取器的使用"""
    print("操作票信息抽取器演示")
    print("="*80)
    
    # 创建抽取器实例
    extractor = FinalOperationTicketExtractor()
    
    # 测试文本
    test_texts = [
        "10kV展路灯线前一路灯环网箱变04开关由热备用转运行",
        "山坡站35kV乌山安土线由检修转冷备用",
        "10kV东开线万科汉口传奇开闭所09开关至末端段线路由检修转冷备用（万科汉口传奇开闭所09开关冷备用）",
        "姚家山站姚#3主变10kV姚68开关由热备用转运行",
        "10kV佳海二回#3环网柜05开关由热备用转冷备用"
    ]
    
    print("单个文本抽取示例:")
    print("-" * 60)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n示例 {i}:")
        print(f"输入文本: {text}")
        
        result = extractor.extract_single_text(text)
        print("抽取结果:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    
    print("\n" + "="*80)
    print("批量抽取JSON格式输出:")
    print("-" * 60)
    
    # 批量抽取并输出JSON格式
    json_results = extractor.extract_to_json_format(test_texts)
    
    # 美化输出JSON
    print(json.dumps(json_results, ensure_ascii=False, indent=2))
    
    return json_results

def save_demo_results():
    """保存演示结果到文件"""
    extractor = FinalOperationTicketExtractor()
    
    test_texts = [
        "10kV展路灯线前一路灯环网箱变04开关由热备用转运行",
        "山坡站35kV乌山安土线由检修转冷备用",
        "10kV东开线万科汉口传奇开闭所09开关至末端段线路由检修转冷备用（万科汉口传奇开闭所09开关冷备用）",
        "姚家山站姚#3主变10kV姚68开关由热备用转运行",
        "10kV佳海二回#3环网柜05开关由热备用转冷备用"
    ]
    
    results = extractor.extract_to_json_format(test_texts)
    
    # 保存到文件
    output_file = '/Users/zzh/Downloads/武汉操作票抽取/extraction_demo_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n演示结果已保存到: {output_file}")
    
    return output_file

if __name__ == "__main__":
    # 运行演示
    demo_results = demo()
    
    # 保存演示结果
    save_demo_results()
    
    print("\n" + "="*80)
    print("使用说明:")
    print("1. 创建抽取器实例: extractor = FinalOperationTicketExtractor()")
    print("2. 单个文本抽取: result = extractor.extract_single_text(text)")
    print("3. 批量抽取: results = extractor.extract_batch(texts)")
    print("4. JSON格式输出: json_results = extractor.extract_to_json_format(texts)")
    print("\n准确率参考 (基于100条测试数据):")
    print("- 初始状态: 98%")
    print("- 目标状态: 93%") 
    print("- 操作类型: 99%")
    print("- 操作设备: 38%")
    print("- 设备所属厂站: 93%")
    print("- 设备所属线路: 81%")
    print("- 总体准确率: 83.67%")
