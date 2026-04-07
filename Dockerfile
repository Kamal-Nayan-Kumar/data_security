FROM rust:1.80-slim as builder
WORKDIR /app
COPY ./backend/ /app/backend/
COPY ./cli/ /app/cli/
COPY ./Cargo.toml /app/Cargo.toml
COPY ./Cargo.lock /app/Cargo.lock

ENV SQLX_OFFLINE=true
RUN cd backend && cargo build --release

FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libpq-dev \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/backend/target/release/backend /usr/local/bin/backend

COPY ["other memeber work/", "/app/other member work/"]
COPY ./backend/migrations/ /app/migrations/

RUN pip install --no-cache-dir -r "/app/other member work/requirements.txt"

ENV HOST=0.0.0.0
ENV PORT=8080

EXPOSE 8080

CMD ["backend"]