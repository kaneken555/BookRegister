# Dockerfile
FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmariadb-dev \
    pkg-config \
    default-mysql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# 環境変数の設定
ENV DJANGO_SETTINGS_MODULE=bookregister.settings

WORKDIR /app/myproject

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout", "120", "bookregister.wsgi:application"]
