"""Output formatting utilities for review results"""

from config import SERVER_URL


def format_review_output(all_issues: list, project_path: str, source_branch: str) -> str:
    """
    將審查結果格式化為 Markdown
    
    Args:
        all_issues: 問題列表
        project_path: GitLab 專案路徑
        source_branch: 來源分支
    
    Returns:
        str: 格式化的 Markdown 文字
    """
    if not all_issues:
        return "✅ **審查完成，未發現任何問題**\n\n所有檔案都通過了程式碼審查。"
    
    # 按照影響程度排序：高 -> 中 -> 低
    impact_order = {'高': 0, '中': 1, '低': 2}
    all_issues.sort(key=lambda x: impact_order.get(x.get('impact', '未知'), 999))

    # 統計影響程度
    impact_count = {'高': 0, '中': 0, '低': 0}
    for issue in all_issues:
        impact = issue.get('impact', '未知')
        if impact in impact_count:
            impact_count[impact] += 1

    # 生成摘要標題
    summary_header = f"**發現 {len(all_issues)} 個問題**"
    if impact_count['高'] > 0 or impact_count['中'] > 0 or impact_count['低'] > 0:
        summary_header += f" (高: {impact_count['高']}, 中: {impact_count['中']}, 低: {impact_count['低']})"
    
    # 生成表格和詳情
    table_rows = [summary_header, "", "| 影響 | 檔案 | 種類 | 摘要 |", "| --- | --- | --- | --- |"]
    details_sections = []
    
    for idx, issue in enumerate(all_issues, 1):
        # 提取欄位
        category = issue.get('category', '未分類')
        summary = issue.get('summary', issue.get('problem', '')[:30] + '...')
        problem = issue.get('problem', '')
        line_range = issue.get('line_range', '')
        impact = issue.get('impact', '未知')
        suggestion = issue.get('suggestion', '')
        file_path = issue.get('file_path', '')
        
        # 建立檔案連結
        location = _build_file_link(project_path, source_branch, file_path, line_range)
        
        # 表格行：只顯示摘要
        summary_text = summary.replace('|', '\\|').replace('\n', ' ')
        table_rows.append(f"| {impact} | {location} | {category} | {summary_text} |")
        
        # 詳細資訊：完整問題和建議
        impact_icon = {'高': '🔴', '中': '🟡', '低': '⚪'}.get(impact, '🔵')
        detail_section = f"""### {impact_icon} 問題 #{idx} - {file_path} ({category}/{impact})
**位置:** {line_range if line_range else '未指定'}

**問題描述:**  
{problem}

**調整:**  
{suggestion}
"""
        details_sections.append(detail_section)
    
    # 組合表格和折疊區域
    table_text = "\n".join(table_rows)
    details_text = "\n---\n\n".join(details_sections)
    
    return f"""{table_text}

<details>
<summary>📋 點擊查看所有問題的完整詳情</summary>

{details_text}

</details>
"""


def _build_file_link(project_path: str, source_branch: str, file_path: str, line_range: str) -> str:
    """構建 GitLab 檔案連結"""
    if project_path and line_range:
        file_link = f"{SERVER_URL}/{project_path}/-/blob/{source_branch}/{file_path}#{line_range}"
        return f"[{file_path}]({file_link})"
    elif project_path:
        file_link = f"{SERVER_URL}/{project_path}/-/blob/{source_branch}/{file_path}"
        return f"[{file_path}]({file_link})"
    else:
        return f"{file_path} {line_range}" if line_range else file_path
