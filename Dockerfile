# Usa a imagem oficial do Python 3.11 leve (slim)
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala ferramentas básicas necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências do projeto
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código-fonte para o container
COPY . .

# Comando de execução do Bot
CMD ["python", "src/bot.py"]