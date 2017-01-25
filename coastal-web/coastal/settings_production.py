from coastal.django_settings import *
from coastal.apps_settings import *

DEBUG = False

ADMINS = (
    ('Liu Yijun', 'liuyijun@aragoncs.com'),
    ('Ma Biao', 'mabiao@aragoncs.com'),
)

ALLOWED_HOSTS = ['34.195.191.5', 'service.itscoastal.com']

SITE_DOMAIN = 'service.itscoastal.com'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'HOST': 'coastalproddb.cotpsf1ajii0.us-east-1.rds.amazonaws.com',
        'NAME': 'coastal_prod',
        'USER': 'coastal',
        'PASSWORD': 'V9pOOnfm8sHuihcl',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, "logs/coastal.log"),
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'coastal': {
            'handlers': ['file', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

MEDIA_URL = 'http://service.itscoastal.com/media/'

GDAL_LIBRARY_PATH = '/usr/lib/libgdal.so'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

BROKER_URL = 'amqp://localhost'

PLATFORM_APPLICATION_ARN = 'arn:aws:sns:us-west-2:104836645074:app/APNS/Coastal'
