# 使用官方Python 3.11 slim版本作为基础镜像
FROM python:3.11-slim

# 设置容器内的工作目录
WORKDIR /app

# 安装PaddleOCR所需的系统级依赖库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件到容器中
COPY requirements.txt .

# 安装所有Python依赖，并在此阶段预下载PaddleOCR模型以加速后续运行
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)"

# 将应用程序代码和源文件列表复制到容器中
COPY src/ ./src/
COPY source_documents.txt .

# 定义容器启动时执行的主命令
CMD ["python", "src/main.py"]
