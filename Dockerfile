FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 1. Dependências do Sistema
RUN apt-get update && apt-get install -y \
    git \
    libpq-dev \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Instalação Manual das Libs
RUN pip install --upgrade pip && \
    pip install \
    asgiref==3.10.0 \
    boto3==1.42.26 \
    botocore==1.42.26 \
    cachetools==6.2.2 \
    certifi==2025.11.12 \
    charset-normalizer==3.4.4 \
    distlib==0.4.0 \
    Django==5.2.8 \
    django-htmx==1.26.0 \
    django-tenants==3.9.0 \
    filelock==3.20.2 \
    google-api-core==2.28.1 \
    google-api-python-client==2.187.0 \
    google-auth==2.41.1 \
    google-auth-httplib2==0.2.1 \
    google-auth-oauthlib==1.2.3 \
    googleapis-common-protos==1.72.0 \
    gunicorn==23.0.0 \
    httplib2==0.31.0 \
    idna==3.11 \
    jmespath==1.0.1 \
    mysqlclient==2.2.7 \
    oauthlib==3.3.1 \
    packaging==25.0 \
    pillow==12.0.0 \
    platformdirs==4.5.1 \
    proto-plus==1.26.1 \
    protobuf==6.33.1 \
    psycopg2-binary==2.9.11 \
    pyasn1==0.6.1 \
    pyasn1_modules==0.4.2 \
    pyparsing==3.2.5 \
    python-dateutil==2.9.0.post0 \
    python-decouple==3.8 \
    requests==2.32.5 \
    requests-oauthlib==2.0.0 \
    rsa==4.9.1 \
    s3transfer==0.16.0 \
    six==1.17.0 \
    source==1.2.0 \
    sqlparse==0.5.3 \
    tzdata==2025.2 \
    uritemplate==4.2.0 \
    urllib3==2.5.0 \
    virtualenv==20.36.0 \
    whitenoise==6.11.0 \
    django-storages

# 3. Copia o código
COPY . /app/

RUN echo "==========================================" && \
    echo "       LISTANDO ARQUIVOS COPIADOS" && \
    echo "==========================================" && \
    ls -R /app && \
    echo "=========================================="

ENV SECRET_KEY=django-insecure-z3#bm50(&%a4peq8+#o8q@fwv5440o9hz2a)^tw%ou1c$n_in5
ENV DATABASE_NAME=dummy_db
ENV DATABASE_USER=dummy_user
ENV DATABASE_PASSWORD=dummy_password
ENV DATABASE_HOST=localhost
ENV DATABASE_PORT=5432

# 2. Google OAuth
ENV GOOGLE_OAUTH_CLIENT_ID=dummy_google_id
ENV GOOGLE_OAUTH_CLIENT_SECRET=dummy_google_secret

# 3. Email
ENV EMAIL_HOST=localhost
ENV EMAIL_PORT=587
ENV EMAIL_HOST_USER=dummy_email_user
ENV EMAIL_HOST_PASSWORD=dummy_email_password
ENV EMAIL_USE_TLS=True

# 4. Meta / Facebook
ENV META_APP_ID=dummy_meta_id
ENV META_APP_SECRET=dummy_meta_secret
ENV META_ACCESS_TOKEN=dummy_meta_token
ENV META_ACCOUNT_ID=dummy_account_id
ENV META_REDIRECT_URI=http://localhost/dummy-callback

# 5. LinkedIn
ENV LINKEDIN_CLIENT_ID=dummy_linkedin_id
ENV LINKEDIN_CLIENT_SECRET=dummy_linkedin_secret
ENV LINKEDIN_REDIRECT_URI=http://localhost/dummy-linkedin

# 6. TikTok
ENV TIKTOK_CLIENT_KEY=dummy_tiktok_key
ENV TIKTOK_CLIENT_SECRET=dummy_tiktok_secret
ENV TIKTOK_REDIRECT_URI=http://localhost/dummy-tiktok

# 7. Cloudflare R2 (ADICIONADO AQUI)
ENV R2_BUCKET_NAME=dummy_bucket
ENV R2_ENDPOINT_URL=https://dummy.r2.cloudflarestorage.com
ENV R2_ACCESS_KEY_ID=dummy_key_id
ENV R2_SECRET_ACCESS_KEY=dummy_secret_key

# Roda o collectstatic
CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:3000 config.wsgi:application"]
