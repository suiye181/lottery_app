FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY lottery_web.py ./
EXPOSE 5888

# 核心修改：直接指向 /app/ssl/ 目录下的真实证书文件
CMD ["streamlit", "run", "lottery_web.py", "--server.port=5888", "--server.address=0.0.0.0", "--server.sslCertFile=/app/ssl/privkey.pem", "--server.sslKeyFile=/app/ssl/privkey.key"]
