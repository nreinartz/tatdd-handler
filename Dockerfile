
FROM python:3.11-slim-bullseye

LABEL org.opencontainers.image.created=${BUILD_DATE}
LABEL org.opencontainers.image.version="0.0.0"
LABEL org.opencontainers.image.authors="Nico Reinartz <nico.reinartz@rwth-aachen.de>"
LABEL org.opencontainers.image.vendor="Nico Reinartz"
LABEL org.opencontainers.image.title="Trend Detection Bot Handler"
LABEL org.opencontainers.image.description="Bot handler service for the trend detection project"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .

ENV TREND_API_HOST="https://trendbot.milki-psy.dbis.rwth-aachen.de"

CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]