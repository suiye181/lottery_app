# 使用轻量级的 Python 3.12 基础镜像
FROM python:3.12-slim

# 设置容器内的工作目录
WORKDIR /app

# 先复制依赖文件并安装（利用 Docker 缓存加速构建）
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制 FastAPI 核心业务代码 (必须确保你的 Python 文件名叫 main.py)
COPY main.py ./

# 暴露 5888 端口
EXPOSE 5888

# 终极启动命令：使用 uvicorn 启动，并挂载你之前配好的 SSL 证书开启 HTTPS
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5888", "--ssl-certfile", "/app/ssl/fullchain.pem", "--ssl-keyfile", "/app/ssl/privkey.pem"]
