from flask import render_template
from flask_login import login_required, current_user

def init_app(app):
    @app.route('/')
    @login_required
    def index():
        return render_template('index.html', title='Dashboard')