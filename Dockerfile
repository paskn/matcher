
FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY requirements.txt requirements.txt
RUN uv pip install -r requirements.txt --system

COPY app/ /app/app/

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app.main:app"]
