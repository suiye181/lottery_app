FROM python:3.12-slim
WORKDIR /app
COPY lottery_web.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5888
CMD ["streamlit", "run", "lottery_web.py", "--server.port=5888", "--server.address=0.0.0.0"]
