from coastal.django_settings import *
from coastal.apps_settings import *

ADMINS = (
    ('Liu Yijun', 'liuyijun@aragoncs.com'),
    ('Liu Yijun', 'liuy0214@163.com'),
    ('Bi Lixin', 'bilixin@aragoncs.com'),
    ('Ma Biao', 'mabiao@aragoncs.com'),
    ('Wang Yufei', '2837379503@qq.com'),
    ('Wang Chuan', 'wangchuan@aragoncs.com'),
    ('Wang Xudong', 'wangxudong@aragoncs.com'),
)

ALLOWED_HOSTS = ['54.169.88.72', 'service-test.itscoastal.com']

SITE_DOMAIN = 'service-test.itscoastal.com'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'HOST': 'coastalstagingdb.cpuicio8tv4f.ap-southeast-1.rds.amazonaws.com',
        'NAME': 'coastal',
        'USER': 'coastal',
        'PASSWORD': 'TPJLRrxRbB6TuCfQ',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        }
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
            'formatter': 'simple',
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

MEDIA_URL = 'http://service-test.itscoastal.com/media/'

GDAL_LIBRARY_PATH = '/usr/lib/libgdal.so'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

BROKER_URL = 'amqp://localhost'
