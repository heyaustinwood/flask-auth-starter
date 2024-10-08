from flask import render_template, current_app
from flask_mail import Message
from app import mail

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

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    subject = 'Reset Your Password'
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    recipients = [user.email]
    text_body = render_template('email/auth_reset-pass.txt',
                                user=user,
                                token=token)
    send_email(subject, sender, recipients, text_body)

def send_invitation_email(email, inviter, organization, token):
    subject = f'Invited to Join {organization.name}'
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    recipients = [email]
    template_path = 'email/org_invite.txt'
    print(f"Attempting to render template: {template_path}")
    text_body = render_template(template_path,
                                inviter=inviter,
                                organization=organization,
                                token=token)
    print(f"Rendered template content: {text_body}")
    send_email(subject, sender, recipients, text_body)
