from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    reset_password_token = db.Column(db.String(64), index=True)
    reset_password_expiration = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class APIRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    address = db.Column(db.String(256))
    city = db.Column(db.String(128))
    state = db.Column(db.String(64))
    zip_code = db.Column(db.String(20))
    apn = db.Column(db.String(64))
    fips = db.Column(db.String(64))
    service = db.Column(db.String(64))
    response_data = db.Column(db.Text)

    user = db.relationship('User', backref=db.backref('requests', lazy=True))