# Use the stable python:3.11-bullseye base image, which is more reliable than -slim
FROM python:3.11-bullseye

# Set the working directory inside the container
WORKDIR /app

# Set an environment variable to prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies, now including essential build tools like g++ and cmake
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# --- INSTALLATION STEP ---
# Install all Python packages from requirements.txt.
# This is now a separate, dedicated step for better error isolation.
# The --verbose flag will provide detailed output if any package fails.
RUN python -m pip install --no-cache-dir --verbose -r requirements.txt

# --- MODEL PRE-DOWNLOAD STEP ---
# Pre-download and cache the PaddleOCR models.
# This is also a separate step. If the build fails here, we know it's a model download issue.
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)"

# Copy the rest of your application's code into the container
COPY src/ ./src/
COPY source_documents.txt .

# Define the default command to run when the container starts
CMD ["python", "src/main.py"]
