FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --requirement requirements.txt

COPY milu.py .

RUN useradd --create-home --uid 10001 milu
USER milu

ENTRYPOINT ["python", "milu.py"]
CMD ["--bot"]
