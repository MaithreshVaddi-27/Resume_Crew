# Resume Crew — Dockerfile
# Build:  docker build -t resume-crew .
# Run:    docker run -p 7860:7860 --env-file .env resume-crew

FROM python:3.12-slim

WORKDIR /app

# System deps for pypdf / matplotlib / python-docx wheels (minimal).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY samples ./samples

# CrewAI telemetry stays off for privacy.
ENV CREWAI_TRACING_ENABLED=false \
    CREWAI_DISABLE_TELEMETRY=true \
    CREWAI_DISABLE_TRACKING=true \
    OTEL_SDK_DISABLED=true \
    GRADIO_PORT=7860 \
    GRADIO_SHARE=false

EXPOSE 7860

CMD ["resume-crew-ui"]
