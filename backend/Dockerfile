# AuthentiQ API (FastAPI + AI models + Web3)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# CPU-only PyTorch first (the default PyPI wheel pulls ~3 GB of CUDA libraries).
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home --uid 10001 authentiq \
    && mkdir -p /data/uploads \
    && chown -R authentiq /data /app
USER authentiq

ENV UPLOAD_DIR=/data/uploads \
    CONTRACT_STATE_FILE=/data/contract.json

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"

# Create tables + admin account, then serve. One worker: blockchain transactions are
# signed from one account, and one process keeps their nonces in order.
CMD ["sh", "-c", "python -m app.seed_admin && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
