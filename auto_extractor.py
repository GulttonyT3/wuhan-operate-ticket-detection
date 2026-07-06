#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动信息抽取器
基于模式分析结果，自动从操作票文本中抽取结构化信息
"""

import re
import json
from typing import Dict, List, Optional, Tuple
import pandas as pd

class OperationTicketAutoExtractor:
    def __init__(self):
        """初始化自动抽取器"""
        # 基于分析结果定义的抽取规则
        self.patterns = {
            # 状态转换模式
            'state_transition': r'由(.{1,10}?)转(.{1,10}?)(?:[（\(]|$)',
            
            # 设备名称模式
            'device_patterns': [
                r'([^，,。\s]*?开关)(?=由|至|$)',
                r'([^，,。\s]*?闸刀)(?=由|至|$)', 
                r'([^，,。\s]*?PT)(?=由|至|$)',
                r'([^，,。\s]*?线)(?=由|至|$)',
                r'([^，,。\s]*?变)(?=由|至|$)'
            ],
            
            # 厂站名称模式 - 只提取独立的站所
            'station_patterns': [
                r'^([^，,。\s]*?站)(?=\d+kV|\s|$)',
                r'([^，,。\s]*?变电站)',
                r'([^，,。\s]*?变电所)'
            ],
            
            # 线路名称模式
            'line_patterns': [
                r'(\d+kV[^，,。\s]*?线)(?=.*?由)',
                r'(\d+kv[^，,。\s]*?线)(?=.*?由)',
                r'^(\d+kV[^，,。\s]*?线)',
                r'^(\d+kv[^，,。\s]*?线)'
            ],
            
            # 电压等级模式
            'voltage_pattern': r'(\d+kV|\d+kv)'
        }
        
        # 操作类型映射
        self.operation_mapping = {
            '状态转换': ['热备用', '冷备用', '运行', '检修'],
            '拉合操作': ['开', '合', '拉开', '合上', '闭合', '断开'],
            '倒母操作': ['母线'],
            '地线操作': ['地线']
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
        """提取操作设备名称"""
        # 尝试各种设备模式
        for pattern in self.patterns['device_patterns']:
            matches = re.findall(pattern, text)
            if matches:
                # 选择最长的匹配作为设备名称
                device = max(matches, key=len)
                
                # 进一步清理设备名称
                device = self._clean_device_name(device, text)
                if device:
                    return device
        
        return None
    
    def _clean_device_name(self, device: str, full_text: str) -> str:
        """清理设备名称"""
        if not device:
            return ""
        
        # 如果设备名称太短，尝试扩展上下文
        if len(device) < 8:
            # 查找设备在文本中的位置，尝试获取更完整的名称
            device_pos = full_text.find(device)
            if device_pos > 0:
                # 向前查找，获取更完整的设备名称
                start = max(0, device_pos - 20)
                context = full_text[start:device_pos + len(device)]
                
                # 尝试匹配更完整的设备名称
                extended_patterns = [
                    r'([^，,。\s]*?' + re.escape(device) + r')',
                    r'(\S+?' + re.escape(device) + r')'
                ]
                
                for pattern in extended_patterns:
                    match = re.search(pattern, context)
                    if match and len(match.group(1)) > len(device):
                        return match.group(1)
        
        return device
    
    def extract_station_name(self, text: str) -> Optional[str]:
        """提取厂站名称"""
        for pattern in self.patterns['station_patterns']:
            match = re.search(pattern, text)
            if match:
                station = match.group(1)
                # 验证是否是真正的厂站名称（不是设备名称的一部分）
                if self._is_valid_station(station, text):
                    return station
        
        return None
    
    def _is_valid_station(self, station: str, text: str) -> bool:
        """验证是否是有效的厂站名称"""
        # 如果站名出现在文本开头，更可能是厂站
        if text.startswith(station):
            return True
        
        # 如果站名后面紧跟电压等级，更可能是厂站
        station_pos = text.find(station)
        if station_pos >= 0:
            after_station = text[station_pos + len(station):]
            if re.match(r'\d+kV', after_station):
                return True
        
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
            return "状态转换"  # 默认值
        
        # 检查是否是状态转换
        state_keywords = ['热备用', '冷备用', '运行', '检修']
        if initial_state in state_keywords and target_state in state_keywords:
            return "状态转换"
        
        # 检查是否是拉合操作
        switch_keywords = ['开', '合', '拉开', '合上', '闭合', '断开']
        if initial_state in switch_keywords or target_state in switch_keywords:
            return "拉合操作"
        
        # 检查是否是倒母操作
        if '母线' in initial_state or '母线' in target_state:
            return "倒母操作"
        
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
    
    def extract_batch(self, texts: List[str]) -> List[Dict[str, str]]:
        """批量抽取"""
        results = []
        for text in texts:
            result = self.extract_single_text(text)
            results.append(result)
        return results
    
    def evaluate_accuracy(self, test_data: List[Dict]) -> Dict[str, float]:
        """评估抽取准确率"""
        if not test_data:
            return {}
        
        total_samples = len(test_data)
        field_accuracies = {}
        
        fields = ["初始状态", "目标状态", "操作", "操作设备", "设备所属厂站", "设备所属线路"]
        
        for field in fields:
            correct_count = 0
            
            for item in test_data:
                text = item.get('原始文本', '')
                expected = item.get('标注结果', {}).get(field, '')
                
                # 处理None值
                if expected is None:
                    expected = ""
                
                # 自动抽取
                extracted_result = self.extract_single_text(text)
                actual = extracted_result.get(field, '')
                
                # 比较结果
                if str(expected).strip() == str(actual).strip():
                    correct_count += 1
            
            accuracy = correct_count / total_samples
            field_accuracies[field] = accuracy
        
        # 计算总体准确率
        overall_accuracy = sum(field_accuracies.values()) / len(field_accuracies)
        field_accuracies['总体准确率'] = overall_accuracy
        
        return field_accuracies

def test_extractor():
    """测试抽取器"""
    extractor = OperationTicketAutoExtractor()
    
    # 测试样本
    test_texts = [
        "10kV展路灯线前一路灯环网箱变04开关由热备用转运行",
        "山坡站35kV乌山安土线由检修转冷备用", 
        "10kV东开线万科汉口传奇开闭所09开关至末端段线路由检修转冷备用（万科汉口传奇开闭所09开关冷备用）",
        "姚家山站姚#3主变10kV姚68开关由热备用转运行"
    ]
    
    print("自动抽取器测试结果:")
    print("="*80)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n测试样本 {i}:")
        print(f"原始文本: {text}")
        
        result = extractor.extract_single_text(text)
        print("抽取结果:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        print("-" * 60)

def evaluate_on_real_data():
    """在真实数据上评估"""
    # 加载测试数据
    data_file = '/Users/zzh/Downloads/武汉操作票抽取/cczl_annotation_data.json'
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        print(f"加载了 {len(test_data)} 条测试数据")
        
        # 使用前100条数据进行评估（避免计算时间过长）
        sample_data = test_data[:100]
        
        extractor = OperationTicketAutoExtractor()
        accuracies = extractor.evaluate_accuracy(sample_data)
        
        print("\n在真实数据上的准确率评估 (前100条):")
        print("="*50)
        for field, accuracy in accuracies.items():
            print(f"{field}: {accuracy:.2%}")
        
        return accuracies
        
    except Exception as e:
        print(f"评估失败: {e}")
        return {}

def main():
    print("操作票自动信息抽取器")
    print("="*80)
    
    # 1. 基础测试
    test_extractor()
    
    # 2. 真实数据评估
    print("\n" + "="*80)
    evaluate_on_real_data()

if __name__ == "__main__":
    main()
