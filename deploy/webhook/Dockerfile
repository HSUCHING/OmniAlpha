FROM python:3.12-slim

WORKDIR /app

# docker CLI only (daemon via mounted socket). Needed by deploy/scripts/deploy.sh.
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates curl git \
  && curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-27.3.1.tgz \
    | tar -xz -C /usr/local/bin --strip-components=1 docker/docker \
  && mkdir -p /usr/local/lib/docker/cli-plugins \
  && curl -fsSL https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-linux-x86_64 \
    -o /usr/local/lib/docker/cli-plugins/docker-compose \
  && chmod +x /usr/local/lib/docker/cli-plugins/docker-compose \
  && rm -rf /var/lib/apt/lists/*

COPY deploy/webhook/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY deploy/webhook /app/deploy/webhook

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8702
CMD ["uvicorn", "deploy.webhook.app:app", "--host", "0.0.0.0", "--port", "8702"]
