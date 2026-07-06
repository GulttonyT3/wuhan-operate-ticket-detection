#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI抽取器Web接口测试
提供简单的Web界面测试AI抽取功能
"""

from flask import Flask, render_template_string, request, jsonify
from ai_extractor import AIOperationTicketExtractor
import json

app = Flask(__name__)

# 创建全局抽取器实例
extractor = AIOperationTicketExtractor()

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI操作票信息抽取器 - Web测试</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .config-info {
            background: #e8f4fd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #34495e;
        }
        textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            font-family: monospace;
            resize: vertical;
        }
        .btn {
            background: #3498db;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        .btn:hover {
            background: #2980b9;
        }
        .btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            border-radius: 5px;
        }
        .result.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
        }
        .result.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
        }
        .result-item {
            margin-bottom: 10px;
            padding: 8px;
            background: rgba(255,255,255,0.7);
            border-radius: 3px;
        }
        .result-key {
            font-weight: bold;
            color: #2c3e50;
            display: inline-block;
            width: 120px;
        }
        .result-value {
            color: #27ae60;
        }
        .result-empty {
            color: #95a5a6;
            font-style: italic;
        }
        .json-output {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            overflow-x: auto;
            margin-top: 15px;
        }
        .examples {
            margin-top: 20px;
        }
        .example-btn {
            background: #95a5a6;
            color: white;
            padding: 5px 10px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            margin: 2px;
        }
        .example-btn:hover {
            background: #7f8c8d;
        }
        .loading {
            display: none;
            color: #3498db;
            font-style: italic;
        }
        .status {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .status.connected {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.disconnected {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AI操作票信息抽取器</h1>
        
        <div class="config-info">
            <strong>📡 API配置:</strong><br>
            地址: http://192.168.64.19:21018<br>
            模型: sh-ticket-analyse-model-fastchat—1
        </div>
        
        <div id="status" class="status">
            <span id="status-text">🔗 正在检测API连接...</span>
        </div>
        
        <div class="form-group">
            <label for="text-input">📝 操作票文本:</label>
            <textarea id="text-input" rows="4" placeholder="请输入操作票文本，例如：10kV展路灯线前一路灯环网箱变04开关由热备用转运行"></textarea>
        </div>
        
        <div class="form-group">
            <button class="btn" onclick="extractInfo()" id="extract-btn">🤖 开始抽取</button>
            <button class="btn" onclick="clearAll()" style="background: #e74c3c;">🗑️ 清空</button>
            <span class="loading" id="loading">⏳ 正在抽取中...</span>
        </div>
        
        <div class="examples">
            <label>💡 示例文本 (点击使用):</label><br>
            <button class="example-btn" onclick="useExample(0)">基础状态转换</button>
            <button class="example-btn" onclick="useExample(1)">带厂站信息</button>
            <button class="example-btn" onclick="useExample(2)">复杂设备名称</button>
            <button class="example-btn" onclick="useExample(3)">变电站操作</button>
        </div>
        
        <div id="result"></div>
    </div>

    <script>
        // 示例文本
        const examples = [
            "10kV展路灯线前一路灯环网箱变04开关由热备用转运行",
            "山坡站35kV乌山安土线由检修转冷备用",
            "10kV东开线万科汉口传奇开闭所09开关至末端段线路由检修转冷备用（万科汉口传奇开闭所09开关冷备用）",
            "姚家山站姚#3主变10kV姚68开关由热备用转运行"
        ];
        
        // 使用示例文本
        function useExample(index) {
            document.getElementById('text-input').value = examples[index];
        }
        
        // 清空所有内容
        function clearAll() {
            document.getElementById('text-input').value = '';
            document.getElementById('result').innerHTML = '';
        }
        
        // 抽取信息
        async function extractInfo() {
            const text = document.getElementById('text-input').value.trim();
            if (!text) {
                alert('请输入操作票文本');
                return;
            }
            
            const extractBtn = document.getElementById('extract-btn');
            const loading = document.getElementById('loading');
            const resultDiv = document.getElementById('result');
            
            // 显示加载状态
            extractBtn.disabled = true;
            loading.style.display = 'inline';
            resultDiv.innerHTML = '';
            
            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({text: text})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showResult(data.result, text);
                } else {
                    showError(data.error);
                }
                
            } catch (error) {
                showError('网络请求失败: ' + error.message);
            } finally {
                extractBtn.disabled = false;
                loading.style.display = 'none';
            }
        }
        
        // 显示成功结果
        function showResult(result, originalText) {
            const resultDiv = document.getElementById('result');
            
            let html = '<div class="result success">';
            html += '<h3>✅ 抽取成功</h3>';
            html += '<div style="margin-bottom: 15px;"><strong>原文:</strong> ' + originalText + '</div>';
            
            // 显示各字段结果
            const fields = ['初始状态', '目标状态', '操作', '操作设备', '设备所属厂站', '设备所属线路'];
            fields.forEach(field => {
                const value = result[field];
                const displayValue = value ? value : '(空)';
                const valueClass = value ? 'result-value' : 'result-empty';
                
                html += '<div class="result-item">';
                html += '<span class="result-key">' + field + ':</span>';
                html += '<span class="' + valueClass + '">' + displayValue + '</span>';
                html += '</div>';
            });
            
            // JSON输出
            html += '<div class="json-output">';
            html += '<strong>📄 JSON格式:</strong><br>';
            html += '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
            html += '</div>';
            
            html += '</div>';
            resultDiv.innerHTML = html;
        }
        
        // 显示错误结果
        function showError(error) {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '<div class="result error"><h3>❌ 抽取失败</h3><p>' + error + '</p></div>';
        }
        
        // 检查API连接状态
        async function checkConnection() {
            try {
                const response = await fetch('/status');
                const data = await response.json();
                
                const statusDiv = document.getElementById('status');
                const statusText = document.getElementById('status-text');
                
                if (data.connected) {
                    statusDiv.className = 'status connected';
                    statusText.textContent = '✅ API连接正常';
                } else {
                    statusDiv.className = 'status disconnected';
                    statusText.textContent = '❌ API连接失败: ' + data.error;
                }
            } catch (error) {
                const statusDiv = document.getElementById('status');
                const statusText = document.getElementById('status-text');
                statusDiv.className = 'status disconnected';
                statusText.textContent = '❌ 无法连接到服务器';
            }
        }
        
        // 页面加载时检查连接
        window.onload = function() {
            checkConnection();
        };
        
        // 支持Enter键提交
        document.getElementById('text-input').addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                extractInfo();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    """检查API连接状态"""
    try:
        connected = extractor.test_connection()
        return jsonify({
            'connected': connected,
            'error': None if connected else 'API连接失败'
        })
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e)
        })

@app.route('/extract', methods=['POST'])
def extract():
    """抽取信息接口"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({
                'success': False,
                'error': '文本不能为空'
            })
        
        # 调用AI抽取器
        result = extractor.extract_single_text(text)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🌐 启动Web接口测试服务...")
    print("📡 API配置:")
    print("  地址: http://192.168.64.19:21018")
    print("  模型: sh-ticket-analyse-model-fastchat—1")
    print()
    print("🔗 Web界面地址: http://localhost:5000")
    print("💡 使用 Ctrl+C 停止服务")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
