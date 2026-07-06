#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接和数据抽取脚本
从MySQL数据库中提取操作票标注数据
"""

import pymysql
import json
import pandas as pd
from typing import List, Dict, Any
import warnings
warnings.filterwarnings('ignore')

class OperationTicketExtractor:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        """初始化数据库连接参数"""
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
    
    def connect(self):
        """连接数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            print(f"成功连接到数据库 {self.database}")
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("数据库连接已关闭")
    
    def show_table_structure(self, table_name: str):
        """查看表结构"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                print(f"\n表 {table_name} 的结构:")
                print("-" * 60)
                for col in columns:
                    print(f"{col['Field']:<30} {col['Type']:<20} {col['Null']:<10} {col['Key']:<10}")
                return columns
        except Exception as e:
            print(f"查看表结构失败: {e}")
            return None
    
    def get_sample_data(self, table_name: str, limit: int = 5):
        """获取表的样本数据"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                data = cursor.fetchall()
                print(f"\n表 {table_name} 的样本数据 (前{limit}条):")
                print("-" * 100)
                for row in data:
                    print(row)
                return data
        except Exception as e:
            print(f"获取样本数据失败: {e}")
            return None
    
    def extract_cczl_data(self):
        """提取CCZL结尾的数据"""
        try:
            with self.connection.cursor() as cursor:
                # 查询CCZL结尾的数据
                query = """
                SELECT 
                    av.text_id,
                    av.initial_action,
                    av.target_action,
                    av.device_location,
                    av.device_name,
                    av.supply_target_device_name,
                    av.initial_connect_bus_name,
                    tai.text
                FROM t_annotation_val av
                JOIN t_text_annotation_info tai ON av.text_id = tai.id
                WHERE av.text_id LIKE '%CCZL' OR tai.id LIKE '%CCZL'
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                print(f"\n找到 {len(results)} 条CCZL数据")
                return results
                
        except Exception as e:
            print(f"提取CCZL数据失败: {e}")
            return None
    
    def format_extracted_data(self, raw_data: List[Dict]) -> List[Dict]:
        """格式化提取的数据"""
        formatted_data = []
        
        for item in raw_data:
            formatted_item = {
                "text_id": item.get('text_id', ''),
                "原始文本": item.get('text', ''),
                "标注结果": {
                    "初始状态": item.get('initial_action', ''),
                    "目标状态": item.get('target_action', ''),
                    "操作": item.get('device_location', ''),
                    "操作设备": item.get('device_name', ''),
                    "设备所属厂站": item.get('supply_target_device_name', ''),
                    "设备所属线路": item.get('initial_connect_bus_name', '')
                }
            }
            formatted_data.append(formatted_item)
        
        return formatted_data
    
    def save_to_json(self, data: List[Dict], filename: str):
        """保存数据到JSON文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"数据已保存到 {filename}")
        except Exception as e:
            print(f"保存文件失败: {e}")

def main():
    # 数据库配置
    db_config = {
        'host': '192.168.64.58',
        'port': 3306,
        'user': 'root',
        'password': 'tellhow100%',
        'database': 'operate_ticket'
    }
    
    # 创建提取器实例
    extractor = OperationTicketExtractor(**db_config)
    
    try:
        # 连接数据库
        if not extractor.connect():
            return
        
        # 查看表结构
        print("=" * 80)
        print("查看表结构")
        print("=" * 80)
        extractor.show_table_structure('t_annotation_val')
        extractor.show_table_structure('t_text_annotation_info')
        
        # 获取样本数据
        print("\n" + "=" * 80)
        print("获取样本数据")
        print("=" * 80)
        extractor.get_sample_data('t_annotation_val', 3)
        extractor.get_sample_data('t_text_annotation_info', 3)
        
        # 提取CCZL数据
        print("\n" + "=" * 80)
        print("提取CCZL标注数据")
        print("=" * 80)
        cczl_data = extractor.extract_cczl_data()
        
        if cczl_data:
            # 格式化数据
            formatted_data = extractor.format_extracted_data(cczl_data)
            
            # 显示前几条数据
            print("\n前3条格式化数据:")
            for i, item in enumerate(formatted_data[:3]):
                print(f"\n数据 {i+1}:")
                print(f"ID: {item['text_id']}")
                print(f"原始文本: {item['原始文本'][:100]}...")
                print("标注结果:")
                for key, value in item['标注结果'].items():
                    print(f"  {key}: {value}")
            
            # 保存到文件
            filename = '/Users/zzh/Downloads/武汉操作票抽取/cczl_annotation_data.json'
            extractor.save_to_json(formatted_data, filename)
            
            print(f"\n总共提取了 {len(formatted_data)} 条CCZL标注数据")
            
    except Exception as e:
        print(f"执行过程中出错: {e}")
    
    finally:
        # 关闭数据库连接
        extractor.close()

if __name__ == "__main__":
    main()
