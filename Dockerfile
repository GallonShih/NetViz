# 使用 Python 基礎映像
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 複製需求檔案
COPY requirements.txt .

# 安裝需求
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY src/ /app

# 暴露服務端口（假設 Flask 預設使用 8050）
EXPOSE 8050

# 啟動應用程式
CMD ["python", "app.py"]
