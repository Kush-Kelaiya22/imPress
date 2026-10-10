# imPress backend container image (#96).
#
#   docker run -d --name impress -p 8000:8000 -v impress-data:/data ghcr.io/kush-kelaiya22/impress-backend:<version>
#
# linux/amd64 only: backend/requirements-lock.txt (the hash-checked set CI
# tests) is resolved for x86_64. The base image is pinned by digest; update
# the tag comment and the digest together.
# python:3.12-slim
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    IMPRESS_DATABASE_URL=sqlite+aiosqlite:////data/impress.db \
    IMPRESS_FIRMWARE_DIR=/data/firmware_bins \
    IMPRESS_HOST=0.0.0.0 \
    IMPRESS_PORT=8000

WORKDIR /app
COPY backend/requirements-lock.txt backend/requirements-lock.txt
RUN pip install --require-hashes -r backend/requirements-lock.txt

COPY VERSION ./
COPY backend/app backend/app
COPY backend/.env.example backend/.env.example
COPY scripts/init_env.py scripts/docker-entrypoint.sh scripts/

# Unprivileged user. Everything that persists (database, uploaded firmware,
# generated secrets in .env) lives in the /data volume; backend/.env points there.
RUN useradd --system --uid 10001 --home-dir /data --shell /usr/sbin/nologin impress \
    && mkdir -p /data && chown impress:impress /data \
    && ln -s /data/.env backend/.env
USER impress
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import os, ssl, urllib.request as u; s = 'https' if os.environ.get('IMPRESS_SSL_CERTFILE') else 'http'; u.urlopen(f\"{s}://127.0.0.1:{os.environ.get('IMPRESS_PORT', '8000')}/health\", timeout=4, context=ssl._create_unverified_context())"]

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]

LABEL org.opencontainers.image.title="imPress backend" \
      org.opencontainers.image.description="imPress classroom response system: REST API, WebSocket rooms, firmware store and web app" \
      org.opencontainers.image.source="https://github.com/Kush-Kelaiya22/imPress"
