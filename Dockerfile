FROM python:3.11-slim

WORKDIR /app

# Copy requirements dan install library
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code backend
COPY main.py .

# Buka port 8000 untuk FastAPI
EXPOSE 8000

# Jalankan server Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]