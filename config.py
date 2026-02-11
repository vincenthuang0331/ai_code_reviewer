"""Configuration and environment variables for GitLab MR Reviewer"""

import os
import sys


# ---------------------------------------------------------------------------
# Environment Variables
# ---------------------------------------------------------------------------
# GitLab Settings
SERVER_URL = os.getenv("CI_SERVER_URL").rstrip("/")
PROJECT_ID = os.getenv("CI_PROJECT_ID")
MR_IID = os.getenv("CI_MERGE_REQUEST_IID")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")

# LLM Settings
AI_ACCESS_KEY = os.getenv("AI_ACCESS_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")

# General Settings
POST_COMMENT = os.getenv("POST_COMMENT", "true").lower() == "true"

# Batch Processing Settings
MAX_DIFF_CHARS = int(os.getenv("MAX_DIFF_CHARS", "12000"))
MAX_BATCH_CHARS = int(os.getenv("MAX_BATCH_CHARS", "40000"))
MAX_BATCH_FILES = int(os.getenv("MAX_BATCH_FILES", "8"))

# File Filtering
FILE_PATTERN = os.getenv("FILE_PATTERN", r"^src/.*\.cs$")


def get_provider_from_model(model: str) -> str:
    """
    根據模型名稱判斷 LLM 提供商
    
    Args:
        model: 模型名稱 (例如: gpt-4, claude-3-opus, gemini-pro)
    
    Returns:
        str: 提供商名稱 ('openai', 'claude', 'gemini')
    """
    model_lower = model.lower()
    
    if model_lower.startswith("gpt-") or model_lower.startswith("o1-"):
        return "openai"
    elif model_lower.startswith("claude-"):
        return "claude"
    elif model_lower.startswith("gemini-"):
        return "gemini"
    else:
        # 預設為 openai
        return "openai"


def validate_config():
    """驗證必要的環境變數"""
    mandatory = {
        "PROJECT_ID": PROJECT_ID,
        "GITLAB_TOKEN": GITLAB_TOKEN,
        "AI_ACCESS_KEY": AI_ACCESS_KEY,
    }

    missing = [name for name, value in mandatory.items() if not value]
    if missing:
        print("❌ 缺少必要的環境變數:")
        for name in missing:
            print(f"  - {name}")
        sys.exit(1)
