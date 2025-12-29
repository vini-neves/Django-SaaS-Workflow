FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app/
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

# Roda o collectstatic
RUN python manage.py collectstatic --noinput

# Comando final
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "config.wsgi:application"]
