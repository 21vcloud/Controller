"""
Django settings for BareMetalControllerBackend project.

Generated by 'django-admin startproject' using Django 2.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

from BareMetalControllerBackend.conf.env import EnvConfig

env_config = EnvConfig()


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'buhw7wyab8@*+p4p7df%+h&dm2xp(wxmdr6e4wr5akpl&-(=^&'

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True
DEBUG = False
SESSION_COOKIE_DOMAIN = env_config.session_cookie_domain

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_swagger',
    'drf_yasg',
    'baremetal_service',
    'baremetal_openstack',
    'baremetal_dashboard',
    'account',
    'celery_tasks',
    'djcelery',
    'access_control',
    'rest_api',
    'general_feature',
    'baremetal_audit'
    # 'load_balancer'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'BareMetalControllerBackend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['BareMentalWebFont/dist'],
        # 'DIRS': [os.path.join(BASE_DIR, 'unitiled3/templates'), os.path.join(BASE_DIR, 'baremental/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'BareMetalControllerBackend.wsgi.application'

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env_config.backend_mysql_db_name,
        'USER': env_config.backend_mysql_db_user,
        'PASSWORD': env_config.backend_mysql_db_password,
        'HOST': env_config.backend_mysql_db_host,
        'PORT': env_config.backend_mysql_db_port,
        # 'HOST': "124.251.110.196",
        # 'PORT': "9306",
        'ATOMIC_REQUESTS': True
    },
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'
# TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
# STATICFILES_DIRS = (
#     os.path.join(BASE_DIR, "static"),
# )

CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ORIGIN_WHITELIST = (
    '*'
)

CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
    'VIEW',
)

CORS_ALLOW_HEADERS = (
    'XMLHttpRequest',
    'X_FILENAME',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'Pragma',

    # 自定义 headers
    'pro',
    'reg',
)

SWAGGER_SETTINGS = {
    'LOGIN_URL': '/account/login',
    'LOGOUT_URL': '/account/logout',
    'DEFAULT_INFO': 'BareMetalControllerBackend.urls.swagger_info',
    # 'VALIDATOR_URL': 'http://localhost:8189',
    'SECURITY_DEFINITIONS': {
      'api_key': {
         'type': 'apiKey',
         'name': 'Cookie',
         'in': 'header',
      }
        # 'basic': {
        #     'type': 'basic',
        #     'USE_SESSION_AUTH': False
        # }
   },
}


BASE_LOG_DIR = os.path.join(BASE_DIR, "logs")

LOGGING = {
    'version': 1,  # 保留字
    'disable_existing_loggers': False,  # 禁用已经存在的logger实例
    # 日志文件的格式
    'formatters': {
        # request 详细的日志格式
        'request_standard': {
            'format': '[%(asctime)s:] [%(remote_addr)s %(username)s %(request_method)s]'
                      '[%(path_info)s]' '%(message)s ',
        },
        # 详细的日志格式
        'standard': {
            'format': '[%(asctime)s] [task_id:%(name)s] [%(funcName)s] [%(filename)s:%(lineno)d]'
                      '[%(levelname)s] %(message)s'
        },
        # 简单的日志格式
        'simple': {
            'format': '[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] %(message)s'
        },
        # 定义一个特殊的日志格式
        'request_info': {
            'format': '%(message)s'
        }
    },
    # 过滤器
    'filters': {
        'request': {
            '()': 'django_requestlogging.logging_filters.RequestFilter',
        },
    },
    # 处理器
    'handlers': {
        # 在终端打印
        'console': {
            'level': 'DEBUG',
            # 'filters': ['require_debug_true'],  # 只有在Django debug为True时才在屏幕打印日志
            'filters': ['request'],  # 只有在Django debug为True时才在屏幕打印日志
            'class': 'logging.StreamHandler',  #
            'formatter': 'standard'
        },
        # 默认的
        'default': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件，自动切
            'filename': os.path.join(BASE_LOG_DIR, "controller_info.log"),  # 日志文件
            'maxBytes': 1024 * 1024 * 50,  # 日志大小 50M
            'backupCount': 3,  # 最多备份几个
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
        # 专门用来记错误日志
        'error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件，自动切
            'filename': os.path.join(BASE_LOG_DIR, "controller_err.log"),  # 日志文件
            'maxBytes': 1024 * 1024 * 50,  # 日志大小 50M
            'backupCount': 5,
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
        # 专门定义一个收集特定信息的日志
        'request_info': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件，自动切
            'filename': os.path.join(BASE_LOG_DIR, "controller_request_info.log"),
            'maxBytes': 1024 * 1024 * 50,  # 日志大小 50M
            'backupCount': 5,
            'formatter': 'request_standard',
            'encoding': "utf-8"
        }
    },
    'loggers': {
        # 默认的logger应用如下配置
        '': {
            'handlers': ['default', 'error'],  # 上线之后可以把'console'移除
            'level': 'DEBUG',
            'propagate': True,  # 向不向更高级别的logger传递
        },
        # 名为 'request_info'的logger还单独处理
        'request_info': {
            'handlers': ['console', 'request_info'],
            'level': 'INFO',
        }
    },
}
CACHES = {
 'default': {
  'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',  # 指定缓存使用的引擎
  'LOCATION': 'unique-snowflake',         # 写在内存中的变量的唯一值
  'TIMEOUT': 300,             # 缓存超时时间(默认为300秒,None表示永不过期)
  'OPTIONS': {
   'MAX_ENTRIES': 300,           # 最大缓存记录的数量（默认300）
   'CULL_FREQUENCY': 3,          # 缓存到达最大个数之后，剔除缓存个数的比例，即：1/CULL_FREQUENCY（默认3）
  }
 }
}


# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#     }
# }


# access control cfg
DATA_CFG_LIST = [
    'base_bar_data',
    'base_button_data',
    'base_url_data',
]

ROLE_CFG_LIST = [
    'base_bar_role',
    'base_button_role',
    'base_url_role',
]

USER_CFG_LIST = [
    'base_bar_user',
    'base_button_user',
    'base_url_user',
]

ACCESS_CONTROL_OUT = [
    'admin'
]
