from flask import Blueprint

bp = Blueprint('org', __name__)

from app.org import routes
