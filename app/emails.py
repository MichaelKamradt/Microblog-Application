from flask_mail import Message
from app import app, mail # This is mail = Mail(app)
from .decorators import async

@async
def async_send_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    async_send_email(app, msg)

# Make a function that sends out emails as notifications
from flask import render_template
from config import ADMINS

def follower_notifications(followed, follower):
    send_email("[microblog] %s is now following you!" % follower.nickname,
                ADMINS[0],
                [followed.email],
                render_template("follower_email.txt", user = followed, follower=follower),
                render_template("follower_email.html", user = followed, follower = follower))