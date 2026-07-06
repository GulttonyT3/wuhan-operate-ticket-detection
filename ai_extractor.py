#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于大模型API的操作票信息抽取器
使用AI大模型进行更准确的信息抽取
"""

import json
import requests
import time
from typing import Dict, List, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIOperationTicketExtractor:
    """
    基于大模型API的操作票信息抽取器
    """
    
    def __init__(self, api_base_url: str = "http://192.168.64.19:21018", 
                 model_name: str = "sh-ticket-analyse-model-fastchat—1"):
        """
        初始化AI抽取器
        
        Args:
            api_base_url: 大模型API基础URL
            model_name: 模型名称
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.model_name = model_name
        
        # API端点
        self.chat_endpoint = f"{self.api_base_url}/v1/chat/completions"
        
        # 提示词模板 - 根据模型实际表现优化
        self.system_prompt = """你是一个专业的电力操作票信息抽取专家。请从给定的操作票文本中准确抽取以下6个字段的信息：

1. 初始状态：设备操作前的状态（如：热备用、冷备用、运行、检修等）
2. 目标状态：设备操作后的目标状态（如：热备用、冷备用、运行、检修等）
3. 操作：执行的操作类型（如：状态转换、拉合操作、倒母操作等）
4. 操作设备：被操作的具体设备名称
5. 设备所属厂站：设备所属的变电站或开关站名称
6. 设备所属线路：设备所属的线路名称

请用JSON格式输出结果。"""

    def _call_api(self, messages: List[Dict], max_retries: int = 3) -> Optional[str]:
        """
        调用大模型API
        
        Args:
            messages: 对话消息列表
            max_retries: 最大重试次数
            
        Returns:
            模型响应文本
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.1,  # 较低的温度以获得更稳定的输出
            "max_tokens": 500,
            "stream": False
        }
        
        for attempt in range(max_retries):
            try:
                logger.info(f"调用API (尝试 {attempt + 1}/{max_retries})")
                response = requests.post(
                    self.chat_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        logger.info("API调用成功")
                        return content
                    else:
                        logger.error(f"API响应格式异常: {result}")
                else:
                    logger.error(f"API调用失败，状态码: {response.status_code}, 响应: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"API请求异常 (尝试 {attempt + 1}): {e}")
            except Exception as e:
                logger.error(f"未知错误 (尝试 {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
        
        logger.error("API调用失败，已达到最大重试次数")
        return None
    
    def _parse_json_response(self, response_text: str) -> Optional[Dict]:
        """
        解析JSON响应 - 适配模型的实际输出格式
        
        Args:
            response_text: 模型响应文本
            
        Returns:
            解析后的字典
        """
        try:
            # 尝试直接解析JSON
            parsed = json.loads(response_text)
            
            # 如果是数组格式，取第一个元素
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed[0]
            elif isinstance(parsed, dict):
                return parsed
            else:
                logger.error(f"意外的JSON格式: {type(parsed)}")
                return None
                
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            try:
                import re
                
                # 查找JSON数组 [{}]
                array_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
                if array_match:
                    parsed = json.loads(array_match.group(0))
                    if isinstance(parsed, list) and len(parsed) > 0:
                        return parsed[0]
                
                # 查找JSON对象 {}
                object_match = re.search(r'\{.*?\}', response_text, re.DOTALL)
                if object_match:
                    return json.loads(object_match.group(0))
                    
            except json.JSONDecodeError:
                pass
            
            logger.error(f"无法解析JSON响应: {response_text}")
            return None
    
    def extract_single_text(self, text: str) -> Dict[str, str]:
        """
        从单个文本中抽取信息
        
        Args:
            text: 操作票文本
            
        Returns:
            抽取结果字典
        """
        # 构建对话消息
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"请从以下操作票文本中抽取信息：\n\n{text}"}
        ]
        
        # 调用API
        response = self._call_api(messages)
        if not response:
            logger.error("API调用失败，返回空结果")
            return self._get_empty_result()
        
        # 解析响应
        parsed_result = self._parse_json_response(response)
        if not parsed_result:
            logger.error("响应解析失败，返回空结果")
            return self._get_empty_result()
        
        # 验证和标准化结果
        return self._standardize_result(parsed_result)
    
    def _get_empty_result(self) -> Dict[str, str]:
        """获取空结果"""
        return {
            "初始状态": "",
            "目标状态": "",
            "操作": "",
            "操作设备": "",
            "设备所属厂站": "",
            "设备所属线路": ""
        }
    
    def _standardize_result(self, result: Dict) -> Dict[str, str]:
        """
        标准化结果格式
        
        Args:
            result: 原始结果字典
            
        Returns:
            标准化后的结果字典
        """
        standardized = self._get_empty_result()
        
        # 映射字段名（处理可能的字段名变体）
        field_mapping = {
            "初始状态": ["初始状态", "initial_state", "初始"],
            "目标状态": ["目标状态", "target_state", "目标"],
            "操作": ["操作", "operation", "操作类型"],
            "操作设备": ["操作设备", "device_name", "设备名称", "设备"],
            "设备所属厂站": ["设备所属厂站", "station_name", "厂站", "变电站"],
            "设备所属线路": ["设备所属线路", "line_name", "线路", "设备线路", "设备所属线路"]
        }
        
        for std_key, possible_keys in field_mapping.items():
            for key in possible_keys:
                if key in result:
                    value = str(result[key]).strip()
                    if value and value.lower() not in ['null', 'none', 'n/a']:
                        standardized[std_key] = value
                    break
        
        return standardized
    
    def extract_batch(self, texts: List[str], batch_delay: float = 1.0) -> List[Dict[str, str]]:
        """
        批量抽取多个文本
        
        Args:
            texts: 操作票文本列表
            batch_delay: 批次间延迟时间（秒）
            
        Returns:
            抽取结果列表
        """
        results = []
        total = len(texts)
        
        logger.info(f"开始批量抽取，共 {total} 条文本")
        
        for i, text in enumerate(texts, 1):
            logger.info(f"处理第 {i}/{total} 条文本")
            
            result = self.extract_single_text(text)
            results.append(result)
            
            # 添加延迟避免API限流
            if i < total and batch_delay > 0:
                time.sleep(batch_delay)
        
        logger.info(f"批量抽取完成，共处理 {len(results)} 条")
        return results
    
    def extract_to_json_format(self, texts: List[str]) -> List[Dict[str, str]]:
        """
        抽取并输出为JSON格式
        
        Args:
            texts: 操作票文本列表
            
        Returns:
            JSON格式的抽取结果
        """
        return self.extract_batch(texts)
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            连接是否成功
        """
        test_messages = [
            {"role": "user", "content": "你好，请简单回复一下测试连接。"}
        ]
        
        response = self._call_api(test_messages)
        return response is not None

def demo():
    """演示AI抽取器的使用"""
    print("AI操作票信息抽取器演示")
    print("="*80)
    
    # 创建AI抽取器实例
    ai_extractor = AIOperationTicketExtractor()
    
    # 测试连接
    print("测试API连接...")
    if not ai_extractor.test_connection():
        print("❌ API连接失败，请检查：")
        print("1. API服务是否正常运行")
        print("2. 网络连接是否正常")
        print("3. API地址和模型名称是否正确")
        return
    
    print("✅ API连接成功")
    print()
    
    # 测试文本
    test_texts = [
        "10kV展路灯线前一路灯环网箱变04开关由热备用转运行",
        "山坡站35kV乌山安土线由检修转冷备用",
        "10kV东开线万科汉口传奇开闭所09开关至末端段线路由检修转冷备用（万科汉口传奇开闭所09开关冷备用）"
    ]
    
    print("AI抽取测试结果:")
    print("-" * 60)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n示例 {i}:")
        print(f"输入文本: {text}")
        
        result = ai_extractor.extract_single_text(text)
        print("AI抽取结果:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        print("-" * 40)
    
    print("\n批量抽取JSON格式输出:")
    json_results = ai_extractor.extract_to_json_format(test_texts)
    print(json.dumps(json_results, ensure_ascii=False, indent=2))

def compare_with_rule_based():
    """与基于规则的方法进行对比"""
    print("AI抽取器 vs 规则抽取器对比")
    print("="*80)
    
    # 导入规则抽取器
    try:
        from final_extractor import FinalOperationTicketExtractor
        rule_extractor = FinalOperationTicketExtractor()
        print("✅ 规则抽取器加载成功")
    except ImportError:
        print("❌ 无法导入规则抽取器")
        return
    
    # 创建AI抽取器
    ai_extractor = AIOperationTicketExtractor()
    
    # 测试连接
    if not ai_extractor.test_connection():
        print("❌ AI抽取器连接失败")
        return
    
    print("✅ AI抽取器连接成功")
    print()
    
    # 测试文本
    test_texts = [
        "10kV展路灯线前一路灯环网箱变04开关由热备用转运行",
        "山坡站35kV乌山安土线由检修转冷备用"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n测试样本 {i}:")
        print(f"文本: {text}")
        print()
        
        # 规则抽取
        rule_result = rule_extractor.extract_single_text(text)
        print("规则抽取结果:")
        for key, value in rule_result.items():
            print(f"  {key}: {value}")
        
        print()
        
        # AI抽取
        ai_result = ai_extractor.extract_single_text(text)
        print("AI抽取结果:")
        for key, value in ai_result.items():
            print(f"  {key}: {value}")
        
        print("-" * 80)

if __name__ == "__main__":
    # 运行演示
    demo()
    
    print("\n" + "="*80)
    print("使用说明:")
    print("1. 创建AI抽取器: extractor = AIOperationTicketExtractor()")
    print("2. 测试连接: extractor.test_connection()")
    print("3. 单个抽取: result = extractor.extract_single_text(text)")
    print("4. 批量抽取: results = extractor.extract_batch(texts)")
    print("5. JSON输出: json_results = extractor.extract_to_json_format(texts)")
    print("\n配置信息:")
    print(f"- API地址: http://192.168.64.19:21018")
    print(f"- 模型名称: sh-ticket-analyse-model-fastchat—1")
    print(f"- 接口规范: OpenAI Chat Completions API")
