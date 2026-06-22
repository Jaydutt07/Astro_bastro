FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/packages/astro-core:/app/services/api

WORKDIR /app

COPY services/api/requirements.txt /app/services/api/requirements.txt
RUN pip install --no-cache-dir -r /app/services/api/requirements.txt

COPY packages/astro-core /app/packages/astro-core
COPY services/api /app/services/api

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "services/api", "--host", "0.0.0.0", "--port", "8000"]
