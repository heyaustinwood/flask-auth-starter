import os
import secrets
from dotenv import load_dotenv
from datetime import datetime, timedelta

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_migrate import Migrate
from flask_mail import Mail, Message

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Load configuration based on FLASK_ENV
if os.environ.get('FLASK_ENV') == 'development':
    app.config.from_object('config.DevConfig')
else:
    app.config.from_object('config.ProdConfig')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

from models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class SignupForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    accept_terms = BooleanField('I accept the terms and conditions', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset Password')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

@app.route('/')
def home():
    if current_user.is_authenticated:
        return render_template('home.html')
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        flash('Invalid email or password')
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('signup'))
        new_user = User(email=form.email.data)
        new_user.set_password(form.password.data)
        new_user.terms_accepted_at = datetime.utcnow()
        new_user.terms_accepted_ip = request.remote_addr
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.password_reset_token = token
            user.password_reset_expiration = datetime.utcnow() + timedelta(minutes=30)
            db.session.commit()
            
            reset_link = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request',
                          recipients=[user.email])
            msg.body = render_template('emails/password_reset.txt', reset_link=reset_link)
            try:
                mail.send(msg)
            except Exception as e:
                flash('An error occurred while sending the password reset email. Please try again later.')
                return redirect(url_for('forgot_password'))
        flash('If an account with that email exists, we have sent a password reset link.')
        return redirect(url_for('login'))
    return render_template('forgot_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(password_reset_token=token).first()
    if not user or user.password_reset_expiration < datetime.utcnow():
        flash('The password reset link is invalid or has expired. Please request a new one.')
        return redirect(url_for('forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.password_reset_token = None
        user.password_reset_expiration = None
        db.session.commit()
        flash('Your password has been reset successfully. You can now log in with your new password.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('home'))
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/test-email')
def test_email():
    try:
        msg = Message('Test Email',
                      sender=app.config['MAIL_DEFAULT_SENDER'],
                      recipients=['test@example.com'],
                      body='This is a test email from Flask.')
        mail.send(msg)
        return 'Test email sent successfully! Check your logs for details.'
    except Exception as e:
        return f'Failed to send test email: {str(e)}'

if __name__ == '__main__':
    app.run()