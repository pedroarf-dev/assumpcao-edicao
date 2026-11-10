FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir auto-editor faster-whisper
ARG WHISPER_MODEL=small
ENV WHISPER_MODEL=${WHISPER_MODEL}
# baixa o modelo na construção, para o contêiner não depender da internet depois
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('${WHISPER_MODEL}', device='cpu', compute_type='int8')"
WORKDIR /app
COPY edicao /app/edicao
CMD ["python", "/app/edicao/vigia.py"]
