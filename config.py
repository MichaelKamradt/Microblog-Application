# Configurations for the database
import os
basedir = os.path.abspath(os.path.dirname(__file__)) # Basedir is the current directory

if os.environ.get('DATABASE_URL') is None:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db') # Making the app database
else:
    SQLALCHEMY_DATABASE_URI['DATABASE_URL']

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository') # Location of the repository where the migrated files will go
SQLALCHEMY_TRACK_MODIFICATIONS = False # This is being depricated
SQLALCHEMY_RECORD_QUERIES = True # Writes down when a query takes too long
DATABASE_QUERY_TIMEOUT = 0.5 # Threshold of a query, can't take longer than this

# Configurations for the OpenID logins

WTF_CSRF_ENABLED = True # Usually enabled by default, but this turns on Flask-WTForms
SECRET_KEY = 'you-will-never-guess' # This is going to be a secret key at some point

OAUTH_CREDENTIALS = {
    'facebook': {
        'id': '414166015666994',
        'secret': '8f3639a027287e09314544e1dc070dac'
    }
}

# Configuring an email server
# email server settings
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = 'michaelkamradttest@gmail.com'
MAIL_PASSWORD = 'testmichael'

# Administrator list
ADMINS = ['michael.kamradt@gmail.com']

# Define the number of items per page
POSTS_PER_PAGE = 3

# Creating a SQL search database
WHOOSH_BASE = os.path.join(basedir, 'search.db')

# -*- coding: utf-8 -*-
# ...
# Languages available for translation
LANGUAGES = {
    'en': 'English',
    'es': 'Español'
}

# Google Translate Credentials
KEY='AIzaSyCjzi2oRvtNCUMvOw8xxAwuRlJ7A5guB8o'
GOOGLE_CLIENT_ID='909305219139-2lcrf7dflfuvesod4lcs3nb99rfh0kf5.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET='yLOGxG-tCOOh3_JV-JW_O-RI'