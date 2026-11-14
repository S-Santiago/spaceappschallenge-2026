# Public demo image (decision 0006): FastAPI serves the API and the PWA from one origin.
# Built by Hugging Face Spaces from the folder that .github/workflows/deploy-space.yml uploads.
# Local test:  docker build -t farmlens . && docker run --rm -p 8000:7860 farmlens  -> http://localhost:8000
FROM python:3.12-slim

# Spaces run the container as user 1000; the SQLite DB is rebuilt from the committed seeds at every start
# in a writable path (the image itself is read-only for that user).
RUN useradd --create-home --uid 1000 user
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    FIELDSHIFT_DB=/tmp/fieldshift.db

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY web/ web/
COPY data/crops.csv data/crops.csv
COPY data/samples/ data/samples/

USER user
EXPOSE 7860
# --proxy-headers: the host terminates HTTPS in front of the container.
CMD ["sh", "-c", "exec uvicorn fieldshift.api:app --app-dir src --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
