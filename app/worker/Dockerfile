FROM python:3.12.7-slim-bookworm

RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg \
  && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10002 appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD sh -c 'test -f /tmp/heartbeat && [ $(( $(date +%s) - $(cut -d. -f1 /tmp/heartbeat) )) -lt 60 ]'

CMD ["python", "worker.py"]
