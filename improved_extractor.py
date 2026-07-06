#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的自动信息抽取器
基于错误分析，重点改进设备名称抽取
"""

import re
import json
from typing import Dict, List, Optional, Tuple
import pandas as pd

class ImprovedOperationTicketExtractor:
    def __init__(self):
        """初始化改进的抽取器"""
        # 改进后的抽取规则
        self.patterns = {
            # 状态转换模式
            'state_transition': r'由(.{1,10}?)转(.{1,10}?)(?:[（\(]|$)',
            
            # 改进的设备名称抽取策略
            'device_extraction_strategy': 'context_based',  # 基于上下文的策略
            
            # 厂站名称模式 - 更精确
            'station_patterns': [
                r'^([^，,。\s\d]*?站)(?=\d+kV|\s|$)',  # 文本开头的站
                r'([^，,。\s\d]*?变电站)',
                r'([^，,。\s\d]*?变电所)'
            ],
            
            # 线路名称模式 - 更精确
            'line_patterns': [
                r'^(\d+[kK][vV][^，,。\s]*?线)(?=.*?由)',  # 开头的线路名
                r'^(\d+[kK][vV][^，,。\s]*?线)',
            ]
        }
    
    def extract_state_transition(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """提取状态转换信息"""
        match = re.search(self.patterns['state_transition'], text)
        if match:
            initial_state = match.group(1).strip()
            target_state = match.group(2).strip()
            
            # 清理状态中的噪音
            initial_state = self._clean_state(initial_state)
            target_state = self._clean_state(target_state)
            
            return initial_state, target_state
        return None, None
    
    def _clean_state(self, state: str) -> str:
        """清理状态字符串"""
        if not state:
            return ""
        
        # 移除常见的噪音字符
        state = re.sub(r'[（\(].*', '', state)  # 移除括号及其内容
        state = re.sub(r'[，,。].*', '', state)  # 移除逗号后的内容
        state = state.strip()
        
        return state
    
    def extract_device_name(self, text: str) -> Optional[str]:
        """改进的设备名称提取 - 基于上下文分析"""
        
        # 策略1: 找到"由...转..."之前的设备描述
        state_match = re.search(r'(.+?)由.+?转', text)
        if state_match:
            device_context = state_match.group(1).strip()
            
            # 从设备上下文中提取设备名称
            device = self._extract_device_from_context(device_context, text)
            if device:
                return device
        
        # 策略2: 如果策略1失败，使用备用方法
        return self._fallback_device_extraction(text)
    
    def _extract_device_from_context(self, context: str, full_text: str) -> Optional[str]:
        """从设备上下文中提取设备名称"""
        
        # 移除线路前缀（如果存在）
        # 模式：电压等级+线路名
        line_pattern = r'^(\d+[kK][vV][^，,。\s]*?线)'
        line_match = re.match(line_pattern, context)
        
        if line_match:
            line_name = line_match.group(1)
            # 移除线路名称，剩余部分就是设备名称
            device_part = context[len(line_name):].strip()
            if device_part:
                return device_part
        
        # 如果没有明确的线路前缀，查找设备关键词
        device_keywords = ['开关', '闸刀', 'PT', '变', '线']
        
        # 从右向左查找包含设备关键词的最长匹配
        best_device = ""
        for keyword in device_keywords:
            if keyword in context:
                # 找到包含关键词的设备名称
                pattern = rf'([^，,。\s]*?{keyword})'
                matches = re.findall(pattern, context)
                if matches:
                    # 选择最后一个匹配（通常是最完整的设备名称）
                    candidate = matches[-1]
                    if len(candidate) > len(best_device):
                        best_device = candidate
        
        # 如果找到的设备名称太短，尝试扩展
        if best_device and len(best_device) < 6:
            expanded = self._expand_device_name(best_device, context)
            if expanded:
                best_device = expanded
        
        return best_device if best_device else None
    
    def _expand_device_name(self, device: str, context: str) -> str:
        """扩展设备名称"""
        device_pos = context.find(device)
        if device_pos > 0:
            # 向前扩展，获取更完整的设备名称
            start_pos = max(0, device_pos - 15)
            extended_context = context[start_pos:device_pos + len(device)]
            
            # 查找完整的设备名称
            # 设备名称通常不包含逗号、句号等分隔符
            pattern = rf'([^，,。\s]*?{re.escape(device)})'
            match = re.search(pattern, extended_context)
            if match:
                expanded_name = match.group(1)
                if len(expanded_name) > len(device):
                    return expanded_name
        
        return device
    
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
        """提取厂站名称"""
        for pattern in self.patterns['station_patterns']:
            match = re.search(pattern, text)
            if match:
                station = match.group(1)
                # 验证是否是真正的厂站名称
                if self._is_valid_station(station, text):
                    return station
        
        return None
    
    def _is_valid_station(self, station: str, text: str) -> bool:
        """验证是否是有效的厂站名称"""
        # 如果站名出现在文本开头，更可能是厂站
        if text.startswith(station):
            return True
        
        # 排除明显的设备名称
        if len(station) < 3:  # 太短的不太可能是厂站名
            return False
        
        return False
    
    def extract_line_name(self, text: str) -> Optional[str]:
        """提取线路名称"""
        for pattern in self.patterns['line_patterns']:
            match = re.search(pattern, text)
            if match:
                line = match.group(1)
                return line
        
        return None
    
    def determine_operation_type(self, initial_state: str, target_state: str) -> str:
        """根据状态转换确定操作类型"""
        if not initial_state or not target_state:
            return "状态转换"
        
        # 检查是否是状态转换
        state_keywords = ['热备用', '冷备用', '运行', '检修']
        if initial_state in state_keywords and target_state in state_keywords:
            return "状态转换"
        
        # 检查是否是拉合操作
        switch_keywords = ['开', '合', '拉开', '合上', '闭合', '断开']
        if initial_state in switch_keywords or target_state in switch_keywords:
            return "拉合操作"
        
        return "状态转换"
    
    def extract_single_text(self, text: str) -> Dict[str, str]:
        """从单个文本中抽取所有信息"""
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
    
    def evaluate_accuracy(self, test_data: List[Dict]) -> Dict[str, float]:
        """评估抽取准确率"""
        if not test_data:
            return {}
        
        total_samples = len(test_data)
        field_accuracies = {}
        detailed_results = []
        
        fields = ["初始状态", "目标状态", "操作", "操作设备", "设备所属厂站", "设备所属线路"]
        
        for field in fields:
            correct_count = 0
            
            for i, item in enumerate(test_data):
                text = item.get('原始文本', '')
                expected = item.get('标注结果', {}).get(field, '')
                
                # 处理None值
                if expected is None:
                    expected = ""
                
                # 自动抽取
                extracted_result = self.extract_single_text(text)
                actual = extracted_result.get(field, '')
                
                # 比较结果
                is_correct = str(expected).strip() == str(actual).strip()
                if is_correct:
                    correct_count += 1
                
                # 记录详细结果（只记录前10个样本用于分析）
                if i < 10:
                    detailed_results.append({
                        'sample_id': i,
                        'text': text,
                        'field': field,
                        'expected': expected,
                        'actual': actual,
                        'correct': is_correct
                    })
            
            accuracy = correct_count / total_samples
            field_accuracies[field] = accuracy
        
        # 计算总体准确率
        overall_accuracy = sum(field_accuracies.values()) / len(field_accuracies)
        field_accuracies['总体准确率'] = overall_accuracy
        
        return field_accuracies, detailed_results
    
    def analyze_errors(self, detailed_results: List[Dict]) -> None:
        """分析错误样本"""
        print("\n错误分析 (前10个样本):")
        print("="*100)
        
        # 按字段分组错误
        error_by_field = {}
        for result in detailed_results:
            if not result['correct']:
                field = result['field']
                if field not in error_by_field:
                    error_by_field[field] = []
                error_by_field[field].append(result)
        
        for field, errors in error_by_field.items():
            print(f"\n{field} 错误分析:")
            print("-" * 60)
            for error in errors[:5]:  # 只显示前5个错误
                print(f"文本: {error['text']}")
                print(f"期望: '{error['expected']}'")
                print(f"实际: '{error['actual']}'")
                print()

def test_improved_extractor():
    """测试改进的抽取器"""
    extractor = ImprovedOperationTicketExtractor()
    
    # 测试样本
    test_texts = [
        "10kV展路灯线前一路灯环网箱变04开关由热备用转运行",
        "山坡站35kV乌山安土线由检修转冷备用", 
        "10kV东开线万科汉口传奇开闭所09开关至末端段线路由检修转冷备用（万科汉口传奇开闭所09开关冷备用）",
        "姚家山站姚#3主变10kV姚68开关由热备用转运行"
    ]
    
    print("改进的自动抽取器测试结果:")
    print("="*80)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n测试样本 {i}:")
        print(f"原始文本: {text}")
        
        result = extractor.extract_single_text(text)
        print("抽取结果:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        print("-" * 60)

def evaluate_improved_extractor():
    """在真实数据上评估改进的抽取器"""
    data_file = '/Users/zzh/Downloads/武汉操作票抽取/cczl_annotation_data.json'
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        print(f"加载了 {len(test_data)} 条测试数据")
        
        # 使用前100条数据进行评估
        sample_data = test_data[:100]
        
        extractor = ImprovedOperationTicketExtractor()
        accuracies, detailed_results = extractor.evaluate_accuracy(sample_data)
        
        print("\n改进后在真实数据上的准确率评估 (前100条):")
        print("="*50)
        for field, accuracy in accuracies.items():
            print(f"{field}: {accuracy:.2%}")
        
        # 错误分析
        extractor.analyze_errors(detailed_results)
        
        return accuracies
        
    except Exception as e:
        print(f"评估失败: {e}")
        return {}

def main():
    print("改进的操作票自动信息抽取器")
    print("="*80)
    
    # 1. 基础测试
    test_improved_extractor()
    
    # 2. 真实数据评估
    print("\n" + "="*80)
    evaluate_improved_extractor()

if __name__ == "__main__":
    main()
