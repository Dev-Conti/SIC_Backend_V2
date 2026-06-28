# Usa a imagem oficial do Python como base
FROM python:3.11

# Copiar os arquivos da aplicação
WORKDIR /app
COPY . .

# Instalar as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

# Expor a porta 5001 para HTTPS
EXPOSE 5000

# Comando para rodar a aplicação com Gunicorn e SSL
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--reload", "run:app"]
