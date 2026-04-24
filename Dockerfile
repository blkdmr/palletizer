FROM minizinc/minizinc:latest AS minizinc

FROM python:3.13-slim

# Copy MiniZinc + Gecode binaries from the official image
COPY --from=minizinc /usr/local/bin/minizinc /usr/local/bin/minizinc
COPY --from=minizinc /usr/local/bin/fzn-gecode /usr/local/bin/fzn-gecode
COPY --from=minizinc /usr/local/share/minizinc /usr/local/share/minizinc

RUN apt-get update && apt-get install -y libgomp1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV MZN_STDLIB_DIR="/usr/local/share/minizinc"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000
CMD ["python", "app.py"]