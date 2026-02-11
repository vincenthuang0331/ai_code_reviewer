FROM python:3.11-slim

WORKDIR /app

# 安裝依賴
RUN pip install --no-cache-dir \
    openai \
    requests \
    python-gitlab

# 複製審查腳本
COPY review_mr.py .

# 設定執行權限
RUN chmod +x review_mr.py

ENTRYPOINT ["python", "review_mr.py"]
