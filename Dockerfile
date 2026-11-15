# Public demo image (decision 0008): FastAPI serves the API and the PWA from one origin, on Google Cloud Run.
# Deploy: gcloud run deploy farmlens --source . --region europe-southwest1   (Cloud Run sets $PORT, default 8080)
# Local test:  docker build -t farmlens . && docker run --rm -p 8000:8080 farmlens  -> http://localhost:8000
FROM python:3.12-slim

# The container runs as an unprivileged user (uid 1000); the SQLite DB is rebuilt from the committed seeds at every start
# in a writable path (the image itself is read-only for that user).
RUN useradd --create-home --uid 1000 user
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    FIELDSHIFT_DB=/tmp/fieldshift.db

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY web/ web/
COPY data/crops.csv data/crops.csv
COPY data/samples/ data/samples/

USER user
EXPOSE 8080
# --proxy-headers: the host terminates HTTPS in front of the container.
CMD ["sh", "-c", "exec uvicorn fieldshift.api:app --app-dir src --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
