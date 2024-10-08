from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.auth.routes import require_org_permission
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, current_user
from app.models import User, Invitation, UserOrganization
from app import db

def init_app(app):
    @app.route('/')
    @login_required
    def index():
        if not current_user.current_organization_id:
            return redirect(url_for('auth.select_organization'))
        return render_template('index.html', title='Dashboard')

    @app.route('/organization-dashboard')
    @login_required
    @require_org_permission('member')
    def organization_dashboard():
        return render_template('organization_dashboard.html', title='Organization Dashboard')