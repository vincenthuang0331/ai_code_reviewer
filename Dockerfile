FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir requests

COPY config.py .
COPY gitlab_client.py .
COPY prompts.py .
COPY formatter.py .
COPY review_mr.py .
COPY llm/ ./llm/

# 設定執行權限
RUN chmod +x review_mr.py

ENTRYPOINT ["python", "review_mr.py"]
