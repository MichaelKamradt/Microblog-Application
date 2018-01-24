from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import basedir, ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel
import os

app = Flask(__name__) # Create the application from the class 'Flask'
app.config.from_object('config') # With a config file present, we need to tell Flask to find it and use it
lm = LoginManager(app) # Create a user-login function
lm.login_view = 'login' # The url_for() name for where to redirect after not satisfying @login_required
db = SQLAlchemy(app) # Instantiating the app database

mail = Mail(app) # Instantiates the Mail service from Flask
mail = Moment(app) # Instantiates the Moment extension from Flask
babel = Babel(app)

# Setting up email-oriented logging
if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    credentials = None
    if MAIL_USERNAME == MAIL_PASSWORD:
        credentials = (MAIL_USERNAME, MAIL_PASSWORD)
    mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT), 'no-reply@' + MAIL_SERVER, ADMINS, 'microblog failure', credentials)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

# Setting up a logging file
if not app.debug and os.environ.get('HEROKU') is None:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('tmp/microblog.log', 'a', 1 * 1024 * 1024, 10) # We are capping the size of the log file at one megabyte and having 10 backups
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')) # Setting the format that things are logged at
    app.logger.setLevel(logging.INFO) # Logging the start up time
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('microblog start up')

if os.environ.get('HEROKU') is not None:
    import logging
    stream_handler = logging.StreamHandler()
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('microblog start up')

from app import models, views # Import the views and model module from the Flask application