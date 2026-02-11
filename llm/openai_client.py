"""OpenAI client implementation"""

import json
import re
import sys

import requests

from llm.base import LLMClient


class OpenAIClient(LLMClient):
    """OpenAI API 客戶端實作"""
    
    def __init__(self, api_key: str, model: str):
        """
        初始化 OpenAI 客戶端
        
        Args:
            api_key: OpenAI API 金鑰
            model: 模型名稱
        """
        self.api_key = api_key
        self.model = model
    
    def review_code(self, prompt: str) -> list:
        """
        使用 OpenAI API 審查程式碼
        
        Args:
            prompt: 審查 prompt
            
        Returns:
            list: 問題列表
        """
        responses_payload = {
            "model": self.model,
            "input": prompt,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        resp = requests.post(
            "https://api.openai.com/v1/responses",
            json=responses_payload,
            headers=headers,
            timeout=120,
        )
        
        if resp.status_code != 200:
            print(f"❌ OpenAI API 失敗 (HTTP {resp.status_code}): {resp.text}")
            sys.exit(1)
        
        data = resp.json()
        text = self._extract_output_text(data)
        if not text.strip():
            return []
        
        return self._parse_response(text)
    
    def _extract_output_text(self, response: dict) -> str:
        """從 API 回應中提取文字內容"""
        for item in response.get("output", []):
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        return content.get("text", "")
        return ""
    
    def _parse_response(self, text: str) -> list:
        """解析 AI 回應的 JSON"""
        try:
            text = self.fix_invalid_json(text)
            issues = json.loads(text.strip())
            return issues if isinstance(issues, list) else []
        except json.JSONDecodeError:
            print(f"⚠️ 無法解析 JSON 回應: {text}")
            return []
        
    def fix_invalid_json(self, raw: str) -> dict | list:
        """
        修復無效的 JSON 字串（含未跳脫的多行字串值和 markdown 標記）
        """
        # 移除外層的引號和 markdown 標記
        cleaned = raw.strip().strip('"')
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # 找到 suggestion 欄位的值並處理
        # 匹配 "suggestion": " 到物件結束前的 "
        pattern = r'("suggestion":\s*")(.+?)("\s*\n\s*\})'

        def escape_value(match):
            prefix = match.group(1)
            value = match.group(2)
            suffix = match.group(3)
            # 跳脫換行、反斜線、引號
            value = re.sub(r'(?<!\\)"', '\\"', value)  # 只跳脫未跳脫的引號
            return prefix + value + suffix

        fixed = re.sub(pattern, escape_value, cleaned, flags=re.DOTALL)

        # 解析並回傳
        return fixed
