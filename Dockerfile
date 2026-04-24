FROM python:3.13-slim

RUN apt-get update && apt-get install -y wget libgomp1 && \
    wget -q https://github.com/MiniZinc/MiniZinc/releases/download/2.8.5/MiniZinc-2.8.5-linux-x86_64.tar.gz && \
    tar -xzf MiniZinc-2.8.5-linux-x86_64.tar.gz && \
    mv MiniZinc-2.8.5-linux-x86_64 /opt/minizinc && \
    rm MiniZinc-2.8.5-linux-x86_64.tar.gz && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/minizinc/bin:$PATH"
ENV MZN_STDLIB_DIR="/opt/minizinc/share/minizinc"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000
CMD ["python", "app.py"]