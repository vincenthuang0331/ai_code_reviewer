"""Base class for LLM clients"""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """LLM 客戶端抽象類別"""
    
    @abstractmethod
    def review_code(self, prompt: str) -> list:
        """
        呼叫 LLM 進行程式碼審查
        
        Args:
            prompt: 審查 prompt
            
        Returns:
            list: 問題列表，每個問題包含：
                  - file_path: 檔案路徑
                  - category: 問題種類
                  - summary: 問題摘要
                  - problem: 問題詳細描述
                  - line_range: 行數範圍
                  - impact: 影響程度（高/中/低）
                  - suggestion: 修改建議
        """
        pass
