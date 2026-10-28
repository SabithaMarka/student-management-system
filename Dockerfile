# ─────────────────────────────────────────────────────────────────────────────
#  College Student Management System — Flask application image
# ─────────────────────────────────────────────────────────────────────────────
#
#  Build:   docker build -t college-sms .
#  Run:     docker compose up
#
#  Multi-stage approach is intentionally skipped to keep the image readable
#  for a college DevOps project.  The result is a small (~200 MB) Python slim
#  image.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage: final image ────────────────────────────────────────────────────────
FROM python:3.12-slim

# Metadata
LABEL maintainer="college-sms"
LABEL description="College Student Management System – Flask + MySQL"

# ── System dependencies ───────────────────────────────────────────────────────
# - curl & wget  : used by the health-check in docker-compose
# - default-libmysqlclient-dev + pkg-config: needed to compile the
#   `cryptography` wheel on some architectures (no-op on x86_64 wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        wget \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# ── Python environment ────────────────────────────────────────────────────────
# Prevent .pyc files and enable unbuffered stdout/stderr (shows logs live)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Install dependencies first (cached layer) ────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ── Copy the application source ────────────────────────────────────────────────
COPY . .

# ── Entrypoint ────────────────────────────────────────────────────────────────
# The entrypoint script waits for MySQL to be ready before starting Flask.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ── Expose the Flask port ─────────────────────────────────────────────────────
EXPOSE 5000

# ── Start ─────────────────────────────────────────────────────────────────────
ENTRYPOINT ["/entrypoint.sh"]
