#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试AI抽取器，查看模型的原始响应
"""

import json
import requests

def debug_api_call():
    """调试API调用，查看原始响应"""
    
    api_url = "http://192.168.64.19:21018/v1/chat/completions"
    model_name = "sh-ticket-analyse-model-fastchat—1"
    
    # 简化的提示词
    system_prompt = """你是一个电力操作票信息抽取专家。请从操作票文本中抽取以下信息：
1. 初始状态
2. 目标状态  
3. 操作类型
4. 操作设备
5. 设备所属厂站
6. 设备所属线路

请用JSON格式回答。"""
    
    test_text = "10kV展路灯线前一路灯环网箱变04开关由热备用转运行"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请分析这个操作票文本：{test_text}"}
    ]
    
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 500,
        "stream": False
    }
    
    headers = {"Content-Type": "application/json"}
    
    print("发送请求...")
    print(f"API URL: {api_url}")
    print(f"模型: {model_name}")
    print(f"测试文本: {test_text}")
    print()
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        print("原始响应:")
        print(response.text)
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("解析后的响应:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print("\n模型输出内容:")
                print(content)
                print()
                
                # 尝试解析JSON
                try:
                    json_content = json.loads(content)
                    print("成功解析为JSON:")
                    print(json.dumps(json_content, ensure_ascii=False, indent=2))
                except json.JSONDecodeError:
                    print("无法解析为JSON，尝试提取JSON部分...")
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        try:
                            json_content = json.loads(json_match.group(0))
                            print("提取的JSON:")
                            print(json.dumps(json_content, ensure_ascii=False, indent=2))
                        except json.JSONDecodeError:
                            print("提取的部分也无法解析为JSON")
                    else:
                        print("未找到JSON格式内容")
        else:
            print("API调用失败")
            
    except Exception as e:
        print(f"请求异常: {e}")

def test_different_prompts():
    """测试不同的提示词"""
    
    api_url = "http://192.168.64.19:21018/v1/chat/completions"
    model_name = "sh-ticket-analyse-model-fastchat—1"
    test_text = "10kV展路灯线前一路灯环网箱变04开关由热备用转运行"
    
    # 测试不同的提示词
    prompts = [
        # 简单直接的提示词
        "请分析这个电力操作票文本，告诉我设备的初始状态和目标状态：",
        
        # 更具体的提示词
        """这是一个电力操作票文本。请分析并回答：
1. 设备的初始状态是什么？
2. 设备的目标状态是什么？
3. 操作的设备名称是什么？""",
        
        # 中文专业提示词
        """你是电力系统专家。请分析以下操作票文本，提取关键信息：
文本：{text}

请回答：
- 初始状态：
- 目标状态：
- 操作设备：""",
    ]
    
    for i, prompt_template in enumerate(prompts, 1):
        print(f"\n{'='*60}")
        print(f"测试提示词 {i}")
        print(f"{'='*60}")
        
        if "{text}" in prompt_template:
            prompt = prompt_template.format(text=test_text)
        else:
            prompt = prompt_template + "\n\n" + test_text
        
        messages = [{"role": "user", "content": prompt}]
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 300,
            "stream": False
        }
        
        try:
            response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"提示词: {prompt[:100]}...")
                print(f"模型回复: {content}")
            else:
                print(f"API调用失败: {response.status_code}")
                
        except Exception as e:
            print(f"请求异常: {e}")

if __name__ == "__main__":
    print("调试AI抽取器")
    print("="*80)
    
    # 1. 调试原始API调用
    debug_api_call()
    
    # 2. 测试不同提示词
    test_different_prompts()
