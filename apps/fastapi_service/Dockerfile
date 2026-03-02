FROM python:3.11-slim

WORKDIR /app

# Copy specific requirements file
COPY apps/fastapi_service/requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy only the necessary folders (to avoid copying node_modules or dist)
COPY shared /app/shared
COPY apps/fastapi_service /app/apps/fastapi_service

# Define the python path so modules can be resolved like local dev
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "apps.fastapi_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
