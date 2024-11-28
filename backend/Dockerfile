FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY k4filler_service /app/k4filler_service

CMD ["uvicorn", "k4filler_service.app:app", "--host", "0.0.0.0", "--port", "8000"] 