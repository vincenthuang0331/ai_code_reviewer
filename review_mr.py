#!/usr/bin/env python3
"""GitLab MR reviewer powered by LLM"""

from config import (
    validate_config,
    get_provider_from_model,
    SERVER_URL,
    PROJECT_ID,
    MR_IID,
    AI_ACCESS_KEY,
    AI_MODEL,
    POST_COMMENT,
    MAX_BATCH_CHARS,
    MAX_BATCH_FILES,
    FILE_PATTERN,
)
from gitlab_client import get_mr_diff, post_comment
from llm import get_llm_client
from prompts import build_review_prompt
from formatter import format_review_output


def create_batches(files):
    """將檔案分組為批次"""
    batches = []
    current_batch = []
    current_batch_size = 0
    
    for file_info in files:
        diff_size = len(file_info['diff'])
        
        # 如果單個檔案超過批次限制，單獨處理
        if diff_size > MAX_BATCH_CHARS:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_batch_size = 0
            batches.append([file_info])
        # 如果加入當前批次會超過限制，開始新批次
        elif (current_batch_size + diff_size > MAX_BATCH_CHARS or 
              len(current_batch) >= MAX_BATCH_FILES):
            batches.append(current_batch)
            current_batch = [file_info]
            current_batch_size = diff_size
        # 加入當前批次
        else:
            current_batch.append(file_info)
            current_batch_size += diff_size
    
    # 加入最後一個批次
    if current_batch:
        batches.append(current_batch)
    
    return batches


def process_batches(batches, mr_data, llm_client):
    """處理所有批次並收集問題"""
    all_issues = []
    
    for batch_idx, batch in enumerate(batches, 1):
        file_paths = [f['file_path'] for f in batch]
        if len(batch) == 1:
            print(f"\n[批次 {batch_idx}/{len(batches)}] 正在審查: {file_paths[0]}")
        else:
            print(f"\n[批次 {batch_idx}/{len(batches)}] 正在審查 {len(batch)} 個檔案:")
            for fp in file_paths:
                print(f"  - {fp}")
        
        # 構建 prompt（與 LLM 無關）
        if len(batch) == 1:
            file_info = f"檔案: {batch[0]['file_path']}"
            diff_content = batch[0]['diff']
        else:
            file_info = f"檔案數量: {len(batch)}"
            diff_parts = []
            for fd in batch:
                diff_parts.append(f"\n{'='*80}\n檔案: {fd['file_path']}\n{'='*80}\n{fd['diff']}")
            diff_content = "\n".join(diff_parts)
        
        prompt = build_review_prompt(
            mr_data['title'],
            mr_data['description'],
            file_info,
            diff_content
        )
        
        # 呼叫 LLM 審查
        issues = llm_client.review_code(prompt)
        
        if issues:
            all_issues.extend(issues)
            print(f"✅ 完成審查: 發現 {len(issues)} 個問題")
        else:
            print(f"✅ 完成審查: 無問題")
    
    return all_issues


def main():
    """主程式流程"""
    # 驗證設定
    validate_config()
    
    # 判斷 LLM 提供商
    llm_provider = get_provider_from_model(AI_MODEL)
    
    # 顯示設定資訊
    print("=" * 80)
    print("GitLab MR Code Reviewer")
    print("=" * 80)
    print(f"GitLab URL: {SERVER_URL}")
    print(f"Project ID: {PROJECT_ID}")
    print(f"MR IID: {MR_IID}")
    print(f"LLM Provider: {llm_provider}")
    print(f"AI Model: {AI_MODEL}")
    print(f"Post Comment: {POST_COMMENT}")
    print("=" * 80)
    
    # 建立 LLM 客戶端
    llm_client = get_llm_client(
        model=AI_MODEL,
        api_key=AI_ACCESS_KEY
    )

    # 獲取 MR diff
    mr_data = get_mr_diff()
    file_count = len(mr_data['files'])
    print(f"✅ 成功獲取 MR diff ({file_count} 個符合檔案)")

    if file_count == 0:
        print(f"⚠️ 沒有找到符合模式的檔案 (FILE_PATTERN={FILE_PATTERN})，結束審查。")
        return

    # 批次處理
    batches = create_batches(mr_data['files'])
    print(f"\n📦 已將 {file_count} 個檔案分成 {len(batches)} 個批次處理")
    
    # 處理所有批次
    all_issues = process_batches(batches, mr_data, llm_client)

    # 格式化輸出
    project_path = mr_data.get('project_path', '')
    source_branch = mr_data['source_branch']
    combined_review = format_review_output(all_issues, project_path, source_branch)

    # 顯示結果
    print("\n" + "=" * 80)
    print("審查結果")
    print("=" * 80)
    print(combined_review)
    print("=" * 80)

    # 發佈評論
    post_comment(combined_review)
    print("\n✅ 審查完成！")


if __name__ == "__main__":
    main()
