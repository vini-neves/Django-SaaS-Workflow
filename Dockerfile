# Usa uma imagem leve do Python
FROM python:3.10-slim

# Evita arquivos .pyc e logs presos
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cria a pasta do app
WORKDIR /app

# Instala as dependências
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copia o código do projeto
COPY . /app/

# Roda o collectstatic para arrumar o CSS
RUN python manage.py collectstatic --noinput

# Comando para iniciar (TROQUE 'nome_do_seu_projeto' PELO NOME DA PASTA ONDE ESTÁ O SETTINGS.PY)
CMD ["gunicorn", "--bind", "0.0.0.0:80", "config.wsgi:application"]
