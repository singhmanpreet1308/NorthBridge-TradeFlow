# Build from the PROJECT ROOT (the model lives in the Phase 5 folder):
#   docker build -f "Phase_6_ML Engineering/Dockerfile" -t northbridge-prediction-api .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY ["Phase_6_ML Engineering/requirements-api.txt", "/app/requirements-api.txt"]
RUN pip install --no-cache-dir -r /app/requirements-api.txt

# Keep the same folder layout so app/main.py finds the model via parents[2]
COPY ["Phase_5_Data Science and Predictive Intelligence/notebook/models", "/app/Phase_5_Data Science and Predictive Intelligence/notebook/models"]
COPY ["Phase_6_ML Engineering/app", "/app/Phase_6_ML Engineering/app"]

WORKDIR "/app/Phase_6_ML Engineering"
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
