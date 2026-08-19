# Build from project2-phi-redaction/ as the context, e.g.:
#   docker build -t phi-redaction-proxy -f Dockerfile .
# (docker-compose.yml in this same folder does this for you)

FROM python:3.11-slim

WORKDIR /app

# Install proxy dependencies first, for better layer caching
COPY proxy/requirements.txt ./proxy/requirements.txt
RUN pip install --no-cache-dir -r proxy/requirements.txt \
    && python -m spacy download en_core_web_sm

# Copy the shared vault package (lives one level above proxy/ in the repo
# on purpose - see project2-phi-redaction/proxy/README.md for why)
COPY vault ./vault

# Copy the proxy service itself
COPY proxy ./proxy

# Run from proxy/ so `app.main:app` resolves the same way it does locally,
# with /app (parent of both proxy/ and vault/) on PYTHONPATH so `import vault`
# succeeds the same way PR #79 fixed it for local development.
WORKDIR /app/proxy
ENV PYTHONPATH=/app
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
