FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py

WORKDIR /app

# default-mysql-client provides mysqladmin, used by the entrypoint to wait for the DB
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x docker/entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["docker/entrypoint.sh"]
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
