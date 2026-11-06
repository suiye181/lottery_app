FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY lottery_web.py ./
EXPOSE 5888

# 核心：精准读取 /app/ssl 目录下的 fullchain.pem 和 privkey.pem
CMD ["streamlit", "run", "lottery_web.py", "--server.port=5888", "--server.address=0.0.0.0", "--server.sslCertFile=/app/ssl/fullchain.pem", "--server.sslKeyFile=/app/ssl/privkey.pem"]
