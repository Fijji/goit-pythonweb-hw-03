FROM python:3.9-slim

WORKDIR /app

RUN useradd -m appuser && chown -R appuser /app
USER appuser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 3000

CMD ["python", "main.py"]
