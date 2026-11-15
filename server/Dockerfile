FROM python:3.13-slim
WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/models
# VOICE=1 — поставить свою расшифровку голосовых (Whisper). Нужна только образу бота.
ARG VOICE=0
COPY requirements.txt requirements-voice.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && if [ "$VOICE" = "1" ]; then pip install --no-cache-dir -r requirements-voice.txt; fi
COPY app ./app
COPY bot ./bot
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
