FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Setup wrapper for /bin/sh and /bin/bash so every shell command resolves the dynamic API_SECRET
RUN mv /bin/sh /bin/sh.orig && \
    printf '#!/bin/sh.orig\nif [ -f /shared_secrets/current_secret.txt ]; then export API_SECRET="$(cat /shared_secrets/current_secret.txt 2>/dev/null)"; fi\nexec /bin/sh.orig "$@"\n' > /bin/sh && \
    chmod +x /bin/sh && \
    mv /bin/bash /bin/bash.orig && \
    printf '#!/bin/bash.orig\nif [ -f /shared_secrets/current_secret.txt ]; then export API_SECRET="$(cat /shared_secrets/current_secret.txt 2>/dev/null)"; fi\nexec /bin/bash.orig "$@"\n' > /bin/bash && \
    chmod +x /bin/bash

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
