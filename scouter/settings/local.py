from .base import *

DEBUG = True

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql',
		'NAME': 'scouter',
		'USER': 'eo',
		'PASSWORD': '',
		'HOST': '127.0.0.1',
		'PORT': 5432,
	},
}

# Debug toolbar configuration
INSTALLED_APPS += [
	'debug_toolbar',
]
MIDDLEWARE += [
	'debug_toolbar.middleware.DebugToolbarMiddleware',
]

