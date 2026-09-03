# No apt-get (flaky 502 on some mirrors). docker:cli already has docker + compose plugin.
FROM docker:27-cli

WORKDIR /app

RUN apk add --no-cache python3 py3-pip git \
  && ln -sf /usr/bin/python3 /usr/local/bin/python \
  && ln -sf /usr/bin/pip3 /usr/local/bin/pip

COPY deploy/webhook/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

COPY deploy/webhook /app/deploy/webhook

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8702
CMD ["python3", "-m", "uvicorn", "deploy.webhook.app:app", "--host", "0.0.0.0", "--port", "8702"]
