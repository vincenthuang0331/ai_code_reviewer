"""Claude (Anthropic) client implementation"""

import json
import re
import sys

import requests

from llm.base import LLMClient


class ClaudeClient(LLMClient):
    """Claude API 客戶端實作"""
    
    def __init__(self, api_key: str, model: str):
        """
        初始化 Claude 客戶端
        
        Args:
            api_key: Anthropic API 金鑰
            model: 模型名稱 (例如: claude-3-5-sonnet-20241022)
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = self._get_max_tokens(model)
    
    def _get_max_tokens(self, model: str) -> int:
        """
        根據模型名稱返回最大 token 數
        
        Args:
            model: 模型名稱
            
        Returns:
            int: 最大 output tokens
        """
        model_lower = model.lower()
        
        # Claude 4 系列 (Claself.max_tokensOpus 4.6, Sonnet 4.5, Haiku 4.5)
        if "opus-4" in model_lower:
            return 16384  # Opus 4.6 支持最高 128K
        elif "sonnet-4" in model_lower or "haiku-4" in model_lower:
            return 8192   # Sonnet 4.5 和 Haiku 4.5 支持 64K
        
        # Claude 3.5 系列
        elif "claude-3-5" in model_lower or "claude-3.5" in model_lower:
            return 8192
        
        # Claude 3 系列- 最大 4096
        elif "claude-3" in model_lower:
            return 4096
        
        return 4096
    
    def review_code(self, prompt: str) -> list:
        """
        使用 Claude API 審查程式碼
        
        Args:
            prompt: 審查 prompt
            
        Returns:
            list: 問題列表
        """
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            json=payload,
            headers=headers,
            timeout=120,
        )
        
        if resp.status_code != 200:
            print(f"❌ Claude API 失敗 (HTTP {resp.status_code}): {resp.text}")
            sys.exit(1)
        
        data = resp.json()
        text = self._extract_text(data)
        if not text.strip():
            return []
        
        return self._parse_response(text)
    
    def _extract_text(self, response: dict) -> str:
        """從 API 回應中提取文字內容"""
        content = response.get("content", [])
        if content and isinstance(content, list):
            for item in content:
                if item.get("type") == "text":
                    return item.get("text", "")
        return ""
    
    def _parse_response(self, text: str) -> list:
        """解析 AI 回應的 JSON"""
        try:
            text = self.fix_invalid_json(text)
            issues = json.loads(text.strip())
            return issues
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 解析錯誤: {e}")
            print(f"⚠️ 錯誤位置: 第 {e.lineno} 行, 第 {e.colno} 列")
            
            # 打印問題行及其上下文
            lines = text.split('\n')
            if e.lineno <= len(lines):
                print(f"\n問題行內容:")
                start = max(0, e.lineno - 3)
                end = min(len(lines), e.lineno + 2)
                for i in range(start, end):
                    marker = ">>> " if i == e.lineno - 1 else "    "
                    print(f"{marker}第 {i+1} 行: {repr(lines[i])}")
                    
            # 找出問題欄位
            if e.lineno <= len(lines):
                problem_line = lines[e.lineno - 1]
                import re
                field_match = re.search(r'"([^"]+)":\s*"', problem_line)
                if field_match:
                    print(f"\n可能的問題欄位: {field_match.group(1)}")
            
            return []
        
    def fix_invalid_json(self, raw: str) -> dict | list:
        """
        修復無效的 JSON 字串（含未跳脫的多行字串值和 markdown 標記）
        """
        # 找到第一個 ```json 並移除它及之前的所有內容
        json_start = raw.find("```json")
        if json_start != -1:
            cleaned = raw[json_start + 7:]  # 7 是 "```json" 的長度
        else:
            cleaned = raw

        # 找到最後一個 ``` 並移除它及之後的所有內容
        last_backticks = cleaned.rfind("```")
        if last_backticks != -1:
            cleaned = cleaned[:last_backticks]

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
            value = value.replace('\n', '\\n')  # 只跳脫未跳脫的換行符
            return prefix + value + suffix

        fixed = re.sub(pattern, escape_value, cleaned, flags=re.DOTALL)
        
        return fixed
