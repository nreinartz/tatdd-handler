
FROM python:3.11-slim-bullseye

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .

ENV TREND_API_HOST="https://trendbot.milki-psy.dbis.rwth-aachen.de"

CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]