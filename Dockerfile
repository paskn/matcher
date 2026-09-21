
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY app/ /app/app/

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app.main:app"]
