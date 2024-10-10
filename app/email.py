from flask import render_template, current_app
from flask_mail import Message
from app import mail
from app.models import User

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error sending email: {e}")

def send_email(subject, sender, recipients, text_body):
    print(f"Sending email: Subject: {subject}, Sender: {sender}, Recipients: {recipients}")
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    print(f"Email body: {msg.body}")
    mail.send(msg)

def send_password_reset_email(email, reset_url):
    subject = 'Reset Your Password'
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    recipients = [email]
    text_body = render_template('email/auth_reset-pass.txt',
                                email=email,
                                reset_url=reset_url)
    send_email(subject, sender, recipients, text_body)

def send_invitation_email(email, inviter, organization, token=None):
    if token:
        template_path = 'email/org_invite.txt'
        subject = f'Invite to Join {organization.name}'
    else:
        template_path = 'email/org_invite_existing.txt'
        subject = f'Added to {organization.name}'

    text_body = render_template(template_path,
                                email=email,
                                user=User.query.filter_by(email=email).first(),
                                inviter=inviter,
                                organization=organization,
                                token=token)

    send_email(subject,
               sender=current_app.config['MAIL_DEFAULT_SENDER'],
               recipients=[email],
               text_body=text_body)
