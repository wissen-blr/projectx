# Django settings for myproject project.
import sys

DEBUG = True
TEMPLATE_DEBUG = DEBUG


FACEBOOK_CONSUMER_KEY = "1465581876992854" #QA
FACEBOOK_CONSUMER_SECRET = "240f15b5809a13ebf24cfe21eb66c718" #QA




if (sys.platform == 'linux2'):
       DB_ENGINE="mysql"
       DB_USER="root"
       DB_PASSWORD="wissen"
       DB_NAME="projectx"
       DBFILE_DIR="" 

       APP_HOME_DIR="" 
       APP_LOG_DIR="" 

       SITE_URL = "http://localhost:8000/"
       APP_URL = ""
       NEWS_FILE_PATH=""
    
else:
	DB_ENGINE="sqlite3"
	DB_USER=""
	DB_PASSWORD=""
	DB_NAME="projectx.db"
	DBFILE_DIR="" 

	APP_HOME_DIR="" 
	APP_LOG_DIR="" 

	SITE_URL = "http://localhost:8000/"
	APP_URL = ""
	NEWS_FILE_PATH="" 
	
# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = '/home/wissen/projectx/static_files/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = 'http://app.projectx.com/media/'


ADMINS = (
    # ('Your Name', 'your_email@example.com'),
	('Admin', 'admin@projectx.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.'+DB_ENGINE, # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
         #projectx.db ,             #  Or path to database file if using sqlite3.
        'NAME': DBFILE_DIR + DB_NAME,                      # Or path to database file if using sqlite3.
        'USER': DB_USER,                      # Not used with sqlite3.
        'PASSWORD': DB_PASSWORD,                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True




# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = 'http://app.projectx.com/media/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'a8(w#!d$cemk9i9a@xe=)20qhz&u#mqu9&kbsv+92u0a+&f(ah'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'myproject.urls'

TEMPLATE_DIRS = (
	# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
	# Always use forward slashes, even on Windows.
	# Don't forget to use absolute paths, not relative paths.
	APP_HOME_DIR + "templates"
    #"templates"
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'myproject.mashup',
	'registration',
    #'south',
)

TEMPLATE_CONTEXT_PROCESSORS = (
	'django.contrib.auth.context_processors.auth',
	'django.core.context_processors.static',
)

#User profile
AUTH_PROFILE_MODULE = 'mashup.SBUserProfile'

REGISTRATION_BACKEND = 'registration.backends.default.DefaultBackend'
ACCOUNT_ACTIVATION_DAYS = 10

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'admin@projectx.com'
EMAIL_HOST_PASSWORD = '1jGqDygFER'
DEFAULT_FROM_EMAIL = 'admin@projectx.com'
SERVER_EMAIL = 'admin@projectx.com'
EMAIL_PORT = 587

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

# Global variables used in views.py

NO_SEARCH_RESULTS = 30 # Number of results displayed after doing either Filter search or get_recommendations

LINKEDIN_CONSUMER_KEY = "wpck8uhaonay"
LINKEDIN_CONSUMER_SECRET = "lXF4AovJIVlhEaEJ"
LINKEDIN_CONN_COUNT = 10000 #Limit of how many connections we download when loading LinkedIn data
LINKEDIN_SEARCH_COUNT = 20 #Limit of how many connections we get from LinkedIn Search API 2nd and 3rd degree

FACEBOOK_CONN_COUNT = 10000 #Limit of how many connections we download when loading Facebook data, needed to avoid timeouts
FACEBOOK_NUM_OF_THREADS = 20
FACEBOOK_CONNECTION_STRING = "https://graph.facebook.com/%s?fields=id,first_name,last_name,username,birthday,website,locale,significant_other,languages,education,work,location,hometown,events,groups,likes&"
FACEBOOK_BATCH_CONNECTION_STRING="https://graph.facebook.com/me/friends?fields=id,first_name,last_name,birthday,website,locale,significant_other,languages,education,work,location,hometown,events,interests,likes,picture,groups&limit=20&"
#Mising ones - books,movies,music,groups,activities,albums,feed,games,posts,statuses,tagged

FACEBOOK_SCOPE = "user_education_history,user_events,user_groups,user_likes,user_hometown,user_location,user_work_history,friends_about_me,friends_activities,friends_events,friends_groups,friends_hometown,friends_interests,friends_likes,friends_location,friends_relationships,friends_work_history,friends_education_history"


PROFILE_REFRESH_INTERVAL = 0 #Number of days after which profile is refreshed
TWITTER_CONSUMER_KEY="7kwAPWaK4CAoehnuX9401w"
TWITTER_CONSUMER_SECRET="y7uyaP1Zmn6dowA0Q303aBXhnwqyLtrGjwL4m5kbNs"
TWITTER_CALLBACK_URL=SITE_URL+"twitter_oauth_step2/"
TWITTER_CONN_COUNT = 10000
TWITTER_BATCH_COUNT = 5

NUM_MERGE_THREADS = 1 #used in merging.py merge algorithm

NUM_NEWS_ARTICLES = 15 #used when displaying news articles in connection profile details view


# Additional logging for Projectx
LOGGING = {
	'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
    },
    'handlers': {
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file':{
            'level':'DEBUG',
            'class': 'logging.FileHandler',
            'filename': APP_LOG_DIR + 'projectx.log',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'projectx': {
            'handlers':['file'],
            'propagate': True,
            'level':'DEBUG',
        },
        'django': {
            'handlers':['file'],
            'propagate': True,
            'level':'WARNING',
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        }
    }
}

