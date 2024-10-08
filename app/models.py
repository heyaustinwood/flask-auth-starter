from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
import secrets
from time import time
import jwt
from flask import current_app

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=True, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('UserOrganization', back_populates='organization')

class UserOrganization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    role = db.Column(db.String(50))  # e.g., 'admin', 'member', etc.
    user = db.relationship('User', back_populates='organizations')
    organization = db.relationship('Organization', back_populates='users')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    reset_password_token = db.Column(db.String(64), index=True)
    reset_password_expiration = db.Column(db.DateTime)
    current_organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    organizations = db.relationship('UserOrganization', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    inviter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String(64), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    organization = db.relationship('Organization')
    inviter = db.relationship('User')

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))