from flask import render_template, redirect, url_for, flash, request, g, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import bp
from app.models import User, Organization, UserOrganization, Invitation
from app.email import send_password_reset_email, send_invitation_email
import secrets
from datetime import datetime, timedelta
from sqlalchemy import func
from functools import wraps

def require_org_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_organization:
                current_app.logger.debug(f"No current organization for user {current_user.id}")
                flash('Please select an organization.')
                return redirect(url_for('auth.select_organization'))
            user_org = UserOrganization.query.filter_by(
                user_id=current_user.id,
                organization_id=g.current_organization.id
            ).first()
            current_app.logger.debug(f"User {current_user.id} org role: {user_org.role if user_org else 'None'}")
            if not user_org or (user_org.role != permission and user_org.role != 'admin'):
                current_app.logger.debug(f"Permission denied for user {current_user.id}. Required: {permission}")
                flash('You do not have permission to access this resource.')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.before_app_request
def set_organization_context():
    if current_user.is_authenticated:
        org_id = request.args.get('org_id') or current_user.current_organization_id
        g.current_organization = Organization.query.get(org_id)
        if g.current_organization:
            current_user.current_organization_id = g.current_organization.id
            db.session.commit()

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email').lower()
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'
        user = User.query.filter(func.lower(User.email) == email).first()
        if user is None or not user.check_password(password):
            flash('Invalid email or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=remember_me)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('auth.select_organization')
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
        email = request.form.get('email').lower()
        password = request.form.get('password')
        user = User.query.filter(func.lower(User.email) == email).first()
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

@bp.route('/select-organization', methods=['GET', 'POST'])
@login_required
def select_organization():
    if request.method == 'POST':
        org_id = request.form.get('organization')
        user_org = UserOrganization.query.filter_by(user_id=current_user.id, organization_id=org_id).first()
        if user_org:
            current_user.current_organization_id = org_id
            db.session.commit()
            return redirect(url_for('index'))
        else:
            flash('You do not have access to this organization.')
    organizations = Organization.query.join(UserOrganization).filter(UserOrganization.user_id == current_user.id).all()
    return render_template('auth/select_organization.html', organizations=organizations)

@bp.route('/create-organization', methods=['GET', 'POST'])
@login_required
def create_organization():
    if request.method == 'POST':
        name = request.form.get('name')
        if Organization.query.filter_by(name=name).first():
            flash('An organization with that name already exists.')
            return redirect(url_for('auth.create_organization'))
        org = Organization(name=name)
        db.session.add(org)
        user_org = UserOrganization(user=current_user, organization=org, role='admin')
        db.session.add(user_org)
        db.session.commit()
        flash(f'Organization {name} has been created.')
        return redirect(url_for('auth.select_organization'))
    return render_template('auth/create_organization.html')

@bp.route('/invite', methods=['GET', 'POST'])
@login_required
@require_org_permission('admin')
def invite_user():
    if request.method == 'POST':
        email = request.form.get('email').lower()
        if User.query.filter(func.lower(User.email) == email).first():
            flash('This user is already registered.')
            return redirect(url_for('auth.invite_user'))
        token = Invitation.generate_token()
        invitation = Invitation(email=email, organization_id=g.current_organization.id, inviter_id=current_user.id, token=token)
        db.session.add(invitation)
        db.session.commit()
        send_invitation_email(email, current_user, g.current_organization, token)
        flash(f'Invitation sent to {email}')
        return redirect(url_for('auth.invite_user'))
    return render_template('auth/invite_user.html')

@bp.route('/join/<token>', methods=['GET', 'POST'])
def join_organization(token):
    invitation = Invitation.query.filter_by(token=token).first()
    if not invitation:
        flash('Invalid or expired invitation.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        password = request.form.get('password')
        user = User.query.filter_by(email=invitation.email).first()
        if user:
            flash('You are already registered. Please log in.')
            return redirect(url_for('auth.login'))
        user = User(email=invitation.email)
        user.set_password(password)
        user_org = UserOrganization(user=user, organization_id=invitation.organization_id, role='member')
        db.session.add(user)
        db.session.add(user_org)
        db.session.delete(invitation)
        db.session.commit()
        flash('You have joined the organization. Please log in.')
        return redirect(url_for('auth.login'))
    return render_template('auth/join_organization.html', email=invitation.email)

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email').lower()
        user = User.query.filter(func.lower(User.email) == email).first()
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

@bp.route('/accept_invitation/<token>', methods=['GET', 'POST'])
def accept_invitation(token):
    invitation = Invitation.query.filter_by(token=token).first()
    if not invitation:
        flash('Invalid or expired invitation.')
        return redirect(url_for('index'))

    if current_user.is_authenticated:
        if UserOrganization.query.filter_by(user_id=current_user.id, organization_id=invitation.organization_id).first():
            flash('You are already a member of this organization.')
            return redirect(url_for('index'))
        
        user_org = UserOrganization(user=current_user, organization_id=invitation.organization_id, role='member')
        db.session.add(user_org)
        db.session.delete(invitation)
        db.session.commit()
        flash('You have joined the organization.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        password = request.form.get('password')
        user = User.query.filter_by(email=invitation.email).first()
        
        if user:
            if user.check_password(password):
                login_user(user)
                user_org = UserOrganization(user=user, organization_id=invitation.organization_id, role='member')
                db.session.add(user_org)
                db.session.delete(invitation)
                db.session.commit()
                flash('You have joined the organization.')
                return redirect(url_for('index'))
            else:
                flash('Invalid password.')
        else:
            user = User(email=invitation.email)
            user.set_password(password)
            user_org = UserOrganization(user=user, organization_id=invitation.organization_id, role='member')
            db.session.add(user)
            db.session.add(user_org)
            db.session.delete(invitation)
            db.session.commit()
            login_user(user)
            flash('Your account has been created and you have joined the organization.')
            return redirect(url_for('index'))

    return render_template('auth/accept_invitation.html', email=invitation.email)