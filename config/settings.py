import os
from pathlib import Path
from urllib.parse import urlparse, unquote
BASE_DIR=Path(__file__).resolve().parent.parent
DEBUG=os.getenv('DEBUG','0')=='1'
SECRET_KEY=os.environ.get('SECRET_KEY','')
if len(SECRET_KEY)<50: raise RuntimeError('SECRET_KEY must contain at least 50 random characters')
ALLOWED_HOSTS=os.getenv('ALLOWED_HOSTS','localhost,127.0.0.1').split(',')
if os.getenv('RENDER_EXTERNAL_HOSTNAME'): ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])
CSRF_TRUSTED_ORIGINS=os.getenv('CSRF_TRUSTED_ORIGINS','').split(',') if os.getenv('CSRF_TRUSTED_ORIGINS') else []
INSTALLED_APPS=['django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','core']
MIDDLEWARE=['django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF='config.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','core.views.navigation']}}]
WSGI_APPLICATION='config.wsgi.application'
url=os.getenv('DATABASE_URL','')
if url:
 u=urlparse(url)
 if u.scheme not in ('postgres','postgresql'): raise RuntimeError('PostgreSQL DATABASE_URL required')
 DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':u.path.lstrip('/'),'USER':unquote(u.username or ''),'PASSWORD':unquote(u.password or ''),'HOST':u.hostname,'PORT':u.port or 5432,'CONN_MAX_AGE':60,'OPTIONS':{'sslmode':os.getenv('DB_SSLMODE','require')}}}
else:
 if not DEBUG: raise RuntimeError('Production requires DATABASE_URL')
 DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'local.sqlite3','OPTIONS':{'timeout':20}}}
AUTH_USER_MODEL='core.User'
AUTH_PASSWORD_VALIDATORS=[{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator','OPTIONS':{'min_length':12}},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE='ja'; TIME_ZONE='Asia/Tokyo'; USE_TZ=True
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
LOGIN_URL='/login/'; LOGIN_REDIRECT_URL='/'; LOGOUT_REDIRECT_URL='/login/'
SESSION_COOKIE_AGE=28800; SESSION_COOKIE_HTTPONLY=True; SESSION_COOKIE_SAMESITE='Lax'
SESSION_COOKIE_SECURE=not DEBUG; CSRF_COOKIE_SECURE=not DEBUG
SECURE_SSL_REDIRECT=not DEBUG
SECURE_HSTS_SECONDS=31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS=True; SECURE_HSTS_PRELOAD=True
# Enable only behind a proxy that strips client-supplied Forwarded headers.
if os.getenv('TRUST_PROXY','0')=='1': SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')
SECURE_CONTENT_TYPE_NOSNIFF=True; X_FRAME_OPTIONS='DENY'
DATA_UPLOAD_MAX_MEMORY_SIZE=262144
