"""GitLab API client for MR operations"""

import re
import sys
from urllib.parse import quote

import requests

from config import (
    SERVER_URL,
    PROJECT_ID,
    MR_IID,
    GITLAB_TOKEN,
    POST_COMMENT,
    MAX_DIFF_CHARS,
    FILE_PATTERN,
)


def _request_json(method: str, url: str, **kwargs):
    """通用的 JSON API 請求函數"""
    resp = requests.request(method, url, timeout=60, **kwargs)
    if resp.status_code >= 400:
        print(f"❌ 請求失敗 ({resp.status_code}): {url}\n{resp.text}")
        sys.exit(1)
    return resp.json()


def get_mr_diff():
    """獲取 MR 的 diff 資訊"""
    encoded_project = quote(str(PROJECT_ID), safe="")
    diff_url = f"{SERVER_URL}/api/v4/projects/{encoded_project}/merge_requests/{MR_IID}/changes"
    print(f"正在獲取 MR diff: {diff_url}")
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    data = _request_json("GET", diff_url, headers=headers)

    # 編譯 regex 模式
    try:
        file_pattern = re.compile(FILE_PATTERN)
    except re.error as e:
        print(f"❌ 無效的 FILE_PATTERN regex: {FILE_PATTERN}")
        print(f"   錯誤: {e}")
        sys.exit(1)

    # 收集符合 regex 模式的檔案
    matched_files = []
    for change in data.get("changes", []):
        file_path = change.get('new_path') or change.get('old_path')
        if not file_path:
            continue
        
        # 使用 regex 匹配
        if not file_pattern.search(file_path):
            continue
        
        diff_text = change.get("diff", "")
        if len(diff_text) > MAX_DIFF_CHARS:
            diff_text = diff_text[:MAX_DIFF_CHARS] + "\n\n... (diff truncated)"
            
        matched_files.append({
            "file_path": file_path,
            "diff": diff_text
        })

    author = data.get("author", {})
    return {
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "source_branch": data.get("source_branch", "HEAD"),
        "project_path": data.get("references", {}).get("full", "").split("!")[0] if data.get("references") else "",
        "files": matched_files,
        "requester_username": author.get("username", ""),
        "requester_id": author.get("id"),
    }


def post_comment(review_text: str, requester_username: str = ""):
    """將審查結果發佈為 MR 評論"""
    if not POST_COMMENT:
        print("⚠️ POST_COMMENT=false，僅在終端輸出結果。")
        return

    encoded_project = quote(str(PROJECT_ID), safe="")
    comment_url = f"{SERVER_URL}/api/v4/projects/{encoded_project}/merge_requests/{MR_IID}/notes"
    headers = {
        "PRIVATE-TOKEN": GITLAB_TOKEN,
        "Content-Type": "application/json",
    }
    mention = f"@{requester_username} " if requester_username else ""
    payload = {"body": f"## 🤖 AI Code Review\n\n{mention}{review_text}"}
    resp = requests.post(comment_url, headers=headers, json=payload, timeout=60)
    if resp.status_code in (200, 201):
        print("✅ 已將審查結果留言至 MR。")
    else:
        print(f"⚠️ 無法送出 MR 評論 ({resp.status_code}): {resp.text}")


def reassign_to_requester(requester_id: int):
    """將 MR assignee 改回 requester"""
    if not POST_COMMENT:
        print("⚠️ POST_COMMENT=false，跳過 assignee 更新。")
        return

    encoded_project = quote(str(PROJECT_ID), safe="")
    mr_url = f"{SERVER_URL}/api/v4/projects/{encoded_project}/merge_requests/{MR_IID}"
    headers = {
        "PRIVATE-TOKEN": GITLAB_TOKEN,
        "Content-Type": "application/json",
    }
    resp = requests.put(mr_url, headers=headers, json={"assignee_id": requester_id}, timeout=60)
    if resp.status_code in (200, 201):
        print("✅ 已將 assignee 改回 requester。")
    else:
        print(f"⚠️ 無法更新 assignee ({resp.status_code}): {resp.text}")
