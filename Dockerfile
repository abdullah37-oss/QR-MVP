FROM python:3.13-slim
WORKDIR /app
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY app ./app
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "app.serve"]
