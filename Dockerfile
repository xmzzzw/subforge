FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY pyproject.toml ./
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pydantic pyyaml requests

# 复制代码
COPY app/ ./app/
COPY frontend/ ./frontend/

# 数据目录
ENV SUBFORGE_DATA_DIR=/data
VOLUME /data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
