FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt-lists/*
RUN pip install --no-cache-dir plexapi requests Pillow rapidfuzz Flask rembg onnxruntime
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]