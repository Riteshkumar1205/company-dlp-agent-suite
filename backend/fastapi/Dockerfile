FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV DATABASE_URL=sqlite:///./data/collector.db
ENV STORAGE_PATH=/app/data/uploads
RUN mkdir -p /app/data/uploads
EXPOSE 8443
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8443"]
