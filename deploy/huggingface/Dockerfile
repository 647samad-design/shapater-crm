# Hugging Face Space (Docker). Pulls the backend from the public GitHub repo at build time,
# so this Space only needs these two files (Dockerfile + README.md).
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" PYTHONUNBUFFERED=1

WORKDIR /home/user/app
ARG REPO=https://github.com/647samad-design/shapater-crm.git
RUN git clone --depth 1 $REPO /home/user/src \
    && cp -r /home/user/src/backend/. /home/user/app/ \
    && rm -rf /home/user/src
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860
# Migrate the (external) database, then serve on the port Hugging Face expects.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 7860 --proxy-headers"]
