# AI Code Reviewer

基於 LLM 的 GitLab Merge Request 自動審查工具，支援多種 AI 模型進行程式碼審查。

## ✨ 功能特性

- 從 GitLab API 自動獲取 MR 變更內容
- 支援多種 LLM 模型（OpenAI GPT、Claude、Gemini 等）
- 自動產生繁體中文審查報告
- 自動發布審查結果至 MR 評論
- 支援自訂檔案過濾規則（Regex）
- 批次處理大型 MR（自動分批審查）
- Docker 容器化部署
- 彈性環境變數配置

## 🏗️ 專案結構

```
gitlab-mr-reviewer/
├── review_mr.py          # 主程式入口
├── config.py             # 環境變數與配置管理
├── gitlab_client.py      # GitLab API 客戶端
├── prompts.py            # 審查 Prompt 模板
├── formatter.py          # 輸出格式化工具
├── llm/                  # LLM 客戶端模組
│   ├── __init__.py       # LLM 工廠函式
│   ├── base.py           # 抽象基礎類別
│   └── openai_client.py  # OpenAI 實作
├── Dockerfile            # Docker 映像檔定義
└── README.md             # 說明文件
```

## 🚀 快速開始

### 方式一：直接執行

#### Linux / macOS (Bash)

```bash
# 安裝依賴
pip install requests

# 設定環境變數
export CI_SERVER_URL="https://gitlab.com"
export CI_PROJECT_ID="1234"
export CI_MERGE_REQUEST_IID="5"
export GITLAB_TOKEN="glpat-xxxxx"
export AI_ACCESS_KEY="sk-xxxxx"

# 執行審查
python review_mr.py
```

#### Windows (PowerShell)

```powershell
# 安裝依賴
pip install requests

# 設定環境變數
$env:CI_SERVER_URL="https://gitlab.com"
$env:CI_PROJECT_ID="1234"
$env:CI_MERGE_REQUEST_IID="5"
$env:GITLAB_TOKEN="glpat-xxxxx"
$env:AI_ACCESS_KEY="sk-xxxxx"

# 執行審查
python review_mr.py
```

### 方式二：Docker 容器

```bash
# 建立映像檔
docker build -t gitlab-mr-reviewer .

# 執行容器
docker run --rm \
  -e CI_SERVER_URL="https://gitlab.com" \
  -e CI_PROJECT_ID="your-group/your-project" \
  -e CI_MERGE_REQUEST_IID="123" \
  -e GITLAB_TOKEN="glpat-xxxxx" \
  -e AI_ACCESS_KEY="sk-xxxxx" \
  -e AI_MODEL="gpt-4o-mini" \
  -e POST_COMMENT="true" \
  gitlab-mr-reviewer
```

### 方式三：GitLab CI/CD

在專案的 `.gitlab-ci.yml` 加入：

```yaml
ai-code-review:
  stage: review
  image:
    name: your-registry/gitlab-mr-reviewer:latest
    entrypoint: [""]
  script:
    - python /app/review_mr.py
  variables:
    GITLAB_TOKEN: $CI_JOB_TOKEN
    AI_ACCESS_KEY: $OPENAI_API_KEY
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```

## ⚙️ 環境變數配置

### 必要參數

| 變數名 | 說明 | 範例 |
|--------|------|------|
| `CI_SERVER_URL` | GitLab 伺服器 URL | `https://gitlab.com` |
| `CI_PROJECT_ID` | GitLab 專案 ID 或路徑 | `1234` 或 `group/project` |
| `CI_MERGE_REQUEST_IID` | Merge Request IID | `42` |
| `GITLAB_TOKEN` | GitLab Personal Access Token | `glpat-xxxxx` |
| `AI_ACCESS_KEY` | LLM API 金鑰 | `sk-xxxxx` |

### 可選參數

| 變數名 | 說明 | 預設值 |
|--------|------|--------|
| `AI_MODEL` | LLM 模型名稱 | `gpt-4o-mini` |
| `POST_COMMENT` | 是否發布評論到 MR | `true` |
| `FILE_PATTERN` | 檔案過濾 Regex | `^src/.*\.cs$` |
| `MAX_DIFF_CHARS` | 單檔最大 diff 字元數 | `12000` |
| `MAX_BATCH_CHARS` | 批次最大字元數 | `40000` |
| `MAX_BATCH_FILES` | 批次最大檔案數 | `8` |

## 🎯 審查報告格式

審查報告包含以下資訊：

- **影響程度**：高 / 中 / 低
- **問題分類**：Bug、效能、安全性、可讀性等
- **檔案位置**：完整檔案路徑與行號範圍
- **問題摘要**：簡短描述（10-20 字）
- **詳細說明**：問題的完整描述
- **修改建議**：具體的程式碼改進方案

### 範例輸出

```markdown
## 🤖 AI Code Review

**發現 3 個問題** (高: 1, 中: 1, 低: 1)

| 影響 | 檔案 | 種類 | 摘要 |
| --- | --- | --- | --- |
| 高 | src/DataProcessor.cs (L42-L58) | 效能 | 嵌套迴圈導致 O(n²) 複雜度 |
| 中 | src/ApiClient.cs (L123) | 安全性 | 缺少輸入驗證 |
| 低 | src/Helper.cs (L89) | 可讀性 | 變數命名不清晰 |

<details>
<summary><b>📋 問題 1/3</b> - 嵌套迴圈導致 O(n²) 複雜度</summary>

**檔案**: `src/DataProcessor.cs` (L42-L58)  
**種類**: 效能  
**影響**: 高

#### 問題描述
使用嵌套迴圈會在資料量大時造成效能瓶頸...

#### 建議修改
使用 HashSet 改善查找效率：
\`\`\`csharp
var set = new HashSet<int>(arr2);
foreach (int x in arr1) 
{
    if (set.Contains(x))
        Console.WriteLine($"{x} found");
}
\`\`\`

</details>
```

## 🤖 支援的 LLM 模型

### OpenAI
- `gpt-4o-mini` - 快速且經濟（推薦）
- `gpt-4o` - 更深入的分析
- `gpt-4-turbo` - 平衡版本
- `o1-preview` - 推理模型

### Claude (即將支援)
- `claude-3-opus`
- `claude-3-sonnet`

### Gemini (即將支援)
- `gemini-pro`

## 🔑 權限需求

GitLab Personal Access Token 需要以下權限：
- ✅ `api` - 讀取 MR 和發布評論
- ✅ `read_api` - 讀取專案資訊

## 🛠️ 進階配置

### 自訂檔案過濾

使用 `FILE_PATTERN` 環境變數設定 Regex 過濾規則：

```bash
# 僅審查 src 目錄下的 C# 檔案
FILE_PATTERN="^src/.*\.cs$"

# 審查多種程式語言
FILE_PATTERN="^src/.*\.(cs|py|js|ts)$"

# 排除測試檔案
FILE_PATTERN="^src/(?!.*Test).*\.cs$"
```

### 批次處理設定

針對大型 MR，調整批次處理參數：

```bash
MAX_DIFF_CHARS=12000    # 單檔最大 diff 大小
MAX_BATCH_CHARS=40000   # 單批次最大字元數
MAX_BATCH_FILES=8       # 單批次最大檔案數
```

## 🐛 故障排除

### 問題 1: 無法獲取 MR diff
**症狀**: `❌ 請求失敗 (404)`

**解決方案**:
- 檢查 `GITLAB_TOKEN` 是否有效且未過期
- 確認 `CI_SERVER_URL` 格式正確（例如 `https://gitlab.com`）
- 確認 `CI_PROJECT_ID` 格式正確（可使用數字 ID 或 `group/project` 格式）
- 驗證 `CI_MERGE_REQUEST_IID` 是否存在

### 問題 2: LLM API 錯誤
**症狀**: `❌ OpenAI API 失敗 (HTTP 401)`

**解決方案**:
- 確認 `AI_ACCESS_KEY` 正確
- 檢查 API 配額是否足夠
- 驗證模型名稱拼寫正確

### 問題 3: 無法發布評論
**症狀**: `⚠️ 無法送出 MR 評論`

**解決方案**:
- 確認 `POST_COMMENT=true`
- 檢查 Token 是否有 `api` 權限
- 驗證 MR 狀態是否允許評論



