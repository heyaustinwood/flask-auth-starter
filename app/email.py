from flask_mail import Message
from flask import current_app
from app import mail

def send_password_reset_email(user_email, reset_url):
    msg = Message('Password Reset Request',
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user_email])
    msg.body = f'''To reset your password, visit the following link:

{reset_url}


If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)
