from flask import render_template, redirect, url_for, flash, request
from urllib.parse import urlparse
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp
from app.models import User
from app.email import send_password_reset_email
from flask import current_app
import secrets
from datetime import datetime, timedelta
from sqlalchemy import func

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email').lower()  # Convert email to lowercase
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'
        user = User.query.filter(func.lower(User.email) == email).first()  # Case-insensitive query
        if user is None or not user.check_password(password):
            flash('Invalid email or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=remember_me)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email').lower()  # Convert email to lowercase
        password = request.form.get('password')
        user = User.query.filter(func.lower(User.email) == email).first()  # Case-insensitive query
        if user is not None:
            flash('Please use a different email address.')
            return redirect(url_for('auth.signup'))
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template('auth/signup.html', title='Sign Up')

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email').lower()  # Convert email to lowercase
        user = User.query.filter(func.lower(User.email) == email).first()  # Case-insensitive query
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_password_token = token
            user.reset_password_expiration = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            send_password_reset_email(user.email, reset_url)
            flash('Check your email for the instructions to reset your password')
        else:
            flash('Email address not found')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html', title='Forgot Password')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.query.filter_by(reset_password_token=token).first()
    if user is None or user.reset_password_expiration < datetime.utcnow():
        flash('Invalid or expired reset token')
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if password != password2:
            flash('Passwords do not match')
            return render_template('auth/reset_password.html', title='Reset Password', user_email=user.email)
        user.set_password(password)
        user.reset_password_token = None
        user.reset_password_expiration = None
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', title='Reset Password', user_email=user.email)