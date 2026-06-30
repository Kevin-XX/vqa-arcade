# syntax=docker/dockerfile:1.7
# ============================================================
#  VQA Arcade —— Dockerfile (CPU 版, 完整 7 算法)
#  Python 3.11 slim + torch CPU + opencv-headless
#  最终镜像约 2.5GB
# ============================================================

FROM python:3.11-slim AS base

# ---- 系统依赖(opencv-headless 仍需 libGL/libglib) ----
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- 先装依赖(利用 Docker 层缓存, 改代码不重装) ----
# torch CPU 版: 用官方 CPU index 显著减小体积
RUN pip install --no-cache-dir \
        torch==2.8.0 torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir \
        flask flask-cors numpy Pillow opencv-python-headless

# ---- 复制代码(不含模型, 模型用 volume 挂载) ----
COPY server.py requirements.txt ./
COPY vqa/ ./vqa/
COPY web/ ./web/

# ---- uploads 持久化目录 ----
RUN mkdir -p /app/uploads
VOLUME /app/uploads

# ---- 模型目录(可选: 内置或挂载) ----
# 若镜像内置模型, COPY 时需确保 .dockerignore 不排除 .pth
# 推荐: 用 docker-compose 挂载 vqa/algos/*.pth 到容器, 避免镜像过大
VOLUME /app/vqa/algos

EXPOSE 5100

# gunicorn 不适合流式响应, 用 Flask 内置 threaded 模式
CMD ["python", "server.py"]
