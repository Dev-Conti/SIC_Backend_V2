# Use uma imagem base Python
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema e atualiza a cadeia de certificados do SO
RUN apt-get update && apt-get install -y \
    gcc \
    unixodbc-dev \
    && apt-get install -y --only-upgrade ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de dependências
COPY requirements.txt .

# Atualiza o pip (certifi vendorizado sem as CAs emSign comprometidas) e instala as dependências Python
RUN pip install --no-cache-dir --upgrade "pip>=26.2.2" && \
    pip install --no-cache-dir -r requirements.txt

# Copia todo o código da aplicação
COPY . .

# Expõe a porta da aplicação
EXPOSE 5000

# Define o comando padrão
# Em desenvolvimento (FLASK_ENV=development): usa Flask com hot reload (debug=True)
# Em produção ou outros ambientes: usa gunicorn com --reload para hot reload
CMD ["sh", "-c", "if [ \"$FLASK_ENV\" = \"development\" ]; then python run.py; else gunicorn --bind 0.0.0.0:5000 --workers 1 --timeout 120 --reload run:app; fi"]
