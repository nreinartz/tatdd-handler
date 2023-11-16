
FROM python:3.11-slim-bullseye

LABEL org.opencontainers.image.created=${BUILD_DATE}
LABEL org.opencontainers.image.version="1.0.0-dev.10"
LABEL org.opencontainers.image.authors="Nico Reinartz <nico.reinartz@rwth-aachen.de>"
LABEL org.opencontainers.image.vendor="Nico Reinartz"
LABEL org.opencontainers.image.title="Trend Detection Bot Handler"
LABEL org.opencontainers.image.description="Bot handler service for the trend detection project"
LABEL org.opencontainers.image.source = "https://github.com/nreinartz/tatdd-handler"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .

CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]