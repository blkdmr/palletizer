FROM python:3.13-slim

# Install MiniZinc with Gecode bundled
RUN apt-get update && apt-get install -y wget libgomp1 libgl1 && \
    wget -q https://github.com/MiniZinc/MiniZincIDE/releases/download/2.8.5/MiniZincIDE-2.8.5-bundle-linux-x86_64.tgz && \
    tar -xzf MiniZincIDE-2.8.5-bundle-linux-x86_64.tgz && \
    mv MiniZincIDE-2.8.5-bundle-linux-x86_64 /opt/minizinc && \
    rm MiniZincIDE-2.8.5-bundle-linux-x86_64.tgz && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt-get install -y wget libgomp1 libgl1 libgl1-mesa-glx

ENV PATH="/opt/minizinc/bin:$PATH"
ENV MZN_STDLIB_DIR="/opt/minizinc/share/minizinc"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]