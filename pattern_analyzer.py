#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标注模式分析器
分析人工标注数据中的模式和规律
"""

import json
import re
import pandas as pd
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class PatternAnalyzer:
    def __init__(self, data_file: str):
        """初始化分析器"""
        self.data_file = data_file
        self.data = None
        self.df = None
        self.load_data()
    
    def load_data(self):
        """加载JSON数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"成功加载 {len(self.data)} 条数据")
            
            # 转换为DataFrame便于分析
            rows = []
            for item in self.data:
                row = {
                    'text_id': item['text_id'],
                    'original_text': item['原始文本'],
                    'initial_state': item['标注结果']['初始状态'],
                    'target_state': item['标注结果']['目标状态'],
                    'operation': item['标注结果']['操作'],
                    'device_name': item['标注结果']['操作设备'],
                    'station_name': item['标注结果']['设备所属厂站'],
                    'line_name': item['标注结果']['设备所属线路']
                }
                rows.append(row)
            
            self.df = pd.DataFrame(rows)
            print("数据转换完成")
            
        except Exception as e:
            print(f"加载数据失败: {e}")
    
    def analyze_text_patterns(self):
        """分析文本模式"""
        print("\n" + "="*80)
        print("文本模式分析")
        print("="*80)
        
        # 文本长度分布
        text_lengths = self.df['original_text'].str.len()
        print(f"文本长度统计:")
        print(f"  平均长度: {text_lengths.mean():.1f}")
        print(f"  最短: {text_lengths.min()}")
        print(f"  最长: {text_lengths.max()}")
        print(f"  中位数: {text_lengths.median():.1f}")
        
        # 常见关键词
        all_text = ' '.join(self.df['original_text'].tolist())
        
        # 提取电压等级模式
        voltage_pattern = r'\d+kV'
        voltages = re.findall(voltage_pattern, all_text)
        voltage_counter = Counter(voltages)
        print(f"\n电压等级分布 (前10):")
        for voltage, count in voltage_counter.most_common(10):
            print(f"  {voltage}: {count}")
        
        # 提取状态转换模式
        transition_pattern = r'由(.{1,10})转(.{1,10})'
        transitions = re.findall(transition_pattern, all_text)
        transition_counter = Counter(transitions)
        print(f"\n状态转换模式 (前10):")
        for (from_state, to_state), count in transition_counter.most_common(10):
            print(f"  {from_state} -> {to_state}: {count}")
        
        # 设备类型模式
        device_patterns = [
            r'(\w*开关)',
            r'(\w*闸刀)',
            r'(\w*线)',
            r'(\w*站)',
            r'(\w*所)'
        ]
        
        print(f"\n设备类型模式:")
        for pattern in device_patterns:
            devices = re.findall(pattern, all_text)
            device_counter = Counter(devices)
            device_type = pattern.replace('(\\w*', '').replace(')', '')
            print(f"  {device_type} (前5):")
            for device, count in device_counter.most_common(5):
                if device:  # 过滤空字符串
                    print(f"    {device}: {count}")
    
    def analyze_annotation_patterns(self):
        """分析标注字段模式"""
        print("\n" + "="*80)
        print("标注字段模式分析")
        print("="*80)
        
        # 各字段的值分布
        fields = ['initial_state', 'target_state', 'operation', 'device_name', 'station_name', 'line_name']
        field_names = ['初始状态', '目标状态', '操作', '操作设备', '设备所属厂站', '设备所属线路']
        
        for field, name in zip(fields, field_names):
            print(f"\n{name} 分布:")
            
            # 处理None值
            values = self.df[field].fillna('空值')
            value_counts = values.value_counts()
            
            print(f"  唯一值数量: {len(value_counts)}")
            print(f"  前10个值:")
            for value, count in value_counts.head(10).items():
                print(f"    {value}: {count}")
            
            # 空值统计
            null_count = self.df[field].isnull().sum()
            print(f"  空值数量: {null_count} ({null_count/len(self.df)*100:.1f}%)")
    
    def analyze_text_annotation_mapping(self):
        """分析文本与标注的映射关系"""
        print("\n" + "="*80)
        print("文本与标注映射关系分析")
        print("="*80)
        
        # 分析几个典型样本
        sample_indices = [0, 10, 50, 100, 200]
        
        for i in sample_indices:
            if i < len(self.df):
                print(f"\n样本 {i+1}:")
                print(f"原始文本: {self.df.iloc[i]['original_text']}")
                print("标注结果:")
                print(f"  初始状态: {self.df.iloc[i]['initial_state']}")
                print(f"  目标状态: {self.df.iloc[i]['target_state']}")
                print(f"  操作: {self.df.iloc[i]['operation']}")
                print(f"  操作设备: {self.df.iloc[i]['device_name']}")
                print(f"  设备所属厂站: {self.df.iloc[i]['station_name']}")
                print(f"  设备所属线路: {self.df.iloc[i]['line_name']}")
                print("-" * 60)
    
    def extract_pattern_rules(self):
        """提取模式规则"""
        print("\n" + "="*80)
        print("模式规则提取")
        print("="*80)
        
        rules = []
        
        # 规则1: 状态转换模式
        print("规则1: 状态转换模式识别")
        state_transition_samples = []
        for i, row in self.df.head(20).iterrows():
            text = row['original_text']
            initial = row['initial_state']
            target = row['target_state']
            
            # 查找"由...转..."模式
            pattern = r'由(.{1,10})转(.{1,10})'
            match = re.search(pattern, text)
            if match:
                extracted_initial = match.group(1)
                extracted_target = match.group(2)
                state_transition_samples.append({
                    'text': text,
                    'extracted_initial': extracted_initial,
                    'extracted_target': extracted_target,
                    'labeled_initial': initial,
                    'labeled_target': target,
                    'match': (extracted_initial == initial and extracted_target == target)
                })
        
        print(f"状态转换模式样本分析 (前10个):")
        for sample in state_transition_samples[:10]:
            print(f"  文本: {sample['text']}")
            print(f"  提取: {sample['extracted_initial']} -> {sample['extracted_target']}")
            print(f"  标注: {sample['labeled_initial']} -> {sample['labeled_target']}")
            print(f"  匹配: {'✓' if sample['match'] else '✗'}")
            print()
        
        # 规则2: 设备名称提取模式
        print("规则2: 设备名称提取模式")
        device_patterns = [
            r'(\w+开关)',
            r'(\w+闸刀)', 
            r'(\w+线)',
            r'(\d+kV\w+线)'
        ]
        
        device_extraction_samples = []
        for i, row in self.df.head(20).iterrows():
            text = row['original_text']
            labeled_device = row['device_name']
            
            extracted_devices = []
            for pattern in device_patterns:
                matches = re.findall(pattern, text)
                extracted_devices.extend(matches)
            
            device_extraction_samples.append({
                'text': text,
                'extracted_devices': extracted_devices,
                'labeled_device': labeled_device,
                'contains_labeled': labeled_device in text if labeled_device else False
            })
        
        print(f"设备名称提取样本分析 (前10个):")
        for sample in device_extraction_samples[:10]:
            print(f"  文本: {sample['text']}")
            print(f"  提取设备: {sample['extracted_devices']}")
            print(f"  标注设备: {sample['labeled_device']}")
            print(f"  文本包含标注: {'✓' if sample['contains_labeled'] else '✗'}")
            print()
        
        # 规则3: 厂站名称提取
        print("规则3: 厂站名称提取模式")
        station_patterns = [
            r'(\w+站)',
            r'(\w+所)'
        ]
        
        station_extraction_samples = []
        for i, row in self.df.head(20).iterrows():
            text = row['original_text']
            labeled_station = row['station_name']
            
            extracted_stations = []
            for pattern in station_patterns:
                matches = re.findall(pattern, text)
                extracted_stations.extend(matches)
            
            station_extraction_samples.append({
                'text': text,
                'extracted_stations': extracted_stations,
                'labeled_station': labeled_station,
                'contains_labeled': labeled_station in text if labeled_station else False
            })
        
        print(f"厂站名称提取样本分析 (前10个):")
        for sample in station_extraction_samples[:10]:
            print(f"  文本: {sample['text']}")
            print(f"  提取厂站: {sample['extracted_stations']}")
            print(f"  标注厂站: {sample['labeled_station']}")
            print(f"  文本包含标注: {'✓' if sample['contains_labeled'] else '✗'}")
            print()
        
        return {
            'state_transitions': state_transition_samples,
            'device_extractions': device_extraction_samples,
            'station_extractions': station_extraction_samples
        }
    
    def generate_extraction_rules(self):
        """生成抽取规则总结"""
        print("\n" + "="*80)
        print("抽取规则总结")
        print("="*80)
        
        rules = {
            "状态转换规则": {
                "模式": r"由(.{1,10})转(.{1,10})",
                "说明": "识别'由...转...'模式，提取初始状态和目标状态",
                "示例": "由热备用转运行 -> 初始状态:热备用, 目标状态:运行"
            },
            "设备名称规则": {
                "模式": [
                    r"(\w+开关)",
                    r"(\w+闸刀)",
                    r"(\d+kV\w+线)"
                ],
                "说明": "提取包含开关、闸刀、线路等关键词的设备名称",
                "示例": "前一路灯环网箱变04开关 -> 操作设备:前一路灯环网箱变04开关"
            },
            "厂站名称规则": {
                "模式": [
                    r"(\w+站)",
                    r"(\w+所)"
                ],
                "说明": "提取以'站'或'所'结尾的厂站名称",
                "示例": "山坡站35kV乌山安土线 -> 设备所属厂站:山坡站"
            },
            "线路名称规则": {
                "模式": r"(\d+kV\w+线)",
                "说明": "提取电压等级+线路名称的模式",
                "示例": "10kV展路灯线 -> 设备所属线路:10kV展路灯线"
            },
            "操作类型规则": {
                "模式": "根据状态转换推断",
                "说明": "大多数操作为'状态转换'",
                "示例": "热备用转运行 -> 操作:状态转换"
            }
        }
        
        for rule_name, rule_info in rules.items():
            print(f"\n{rule_name}:")
            print(f"  模式: {rule_info['模式']}")
            print(f"  说明: {rule_info['说明']}")
            print(f"  示例: {rule_info['示例']}")
        
        return rules
    
    def run_full_analysis(self):
        """运行完整分析"""
        print("开始完整的模式分析...")
        
        # 基础统计
        print(f"数据集基本信息:")
        print(f"  总数据量: {len(self.df)}")
        print(f"  字段数量: {len(self.df.columns)}")
        
        # 各项分析
        self.analyze_text_patterns()
        self.analyze_annotation_patterns()
        self.analyze_text_annotation_mapping()
        pattern_samples = self.extract_pattern_rules()
        rules = self.generate_extraction_rules()
        
        return {
            'basic_stats': {
                'total_samples': len(self.df),
                'fields': list(self.df.columns)
            },
            'pattern_samples': pattern_samples,
            'extraction_rules': rules
        }

def main():
    data_file = '/Users/zzh/Downloads/武汉操作票抽取/cczl_annotation_data.json'
    
    analyzer = PatternAnalyzer(data_file)
    results = analyzer.run_full_analysis()
    
    # 保存分析结果
    output_file = '/Users/zzh/Downloads/武汉操作票抽取/pattern_analysis_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n分析结果已保存到: {output_file}")

if __name__ == "__main__":
    main()
