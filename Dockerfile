FROM python:3.12-slim

WORKDIR /app
COPY privacygate /app/privacygate

EXPOSE 8080
USER 65532:65532
CMD ["python", "-m", "privacygate.server", "--host", "0.0.0.0", "--port", "8080"]
