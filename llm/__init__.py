"""LLM client factory"""

import sys

from llm.base import LLMClient
from llm.openai_client import OpenAIClient


def get_llm_client(model: str, api_key: str) -> LLMClient:
    """
    根據模型名稱建立對應的 LLM 客戶端（工廠模式）
    
    Args:
        model: 模型名稱 (例如: gpt-4, claude-3-opus, gemini-pro)
        api_key: API 金鑰
    
    Returns:
        LLMClient: LLM 客戶端實例
    """
    model_lower = model.lower()
    
    # 根據模型前綴判斷提供商
    if model_lower.startswith("gpt-") or model_lower.startswith("o1-"):
        provider = "openai"
    elif model_lower.startswith("claude-"):
        provider = "claude"
    elif model_lower.startswith("gemini-"):
        provider = "gemini"
    else:
        provider = "openai"  # 預設
    
    if provider == "openai":
        if not api_key:
            print("❌ 缺少 OpenAI API 金鑰")
            sys.exit(1)
        return OpenAIClient(api_key=api_key, model=model)
    
    # 未來可以擴展其他 LLM 提供商
    # elif provider == "claude":
    #     return ClaudeClient(api_key=api_key, model=model)
    # elif provider == "gemini":
    #     return GeminiClient(api_key=api_key, model=model)
    
    else:
        print(f"❌ 不支援的 LLM 提供商: {provider} (model: {model})")
        print(f"   支援的模型前綴: gpt-, o1-, claude-, gemini-")
        sys.exit(1)
