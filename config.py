import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'asdf1234'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BATCHDATA_API_URL = os.environ.get('BATCHDATA_API_URL')
    BATCHDATA_API_TOKEN = os.environ.get('BATCHDATA_API_TOKEN')
    BLACKKNIGHT_API_URL = os.environ.get('BLACKKNIGHT_API_URL')
    BLACKKNIGHT_CLIENT_KEY = os.environ.get('BLACKKNIGHT_CLIENT_KEY')
    BLACKKNIGHT_CLIENT_SECRET = os.environ.get('BLACKKNIGHT_CLIENT_SECRET')
    HOUSECANARY_API_URL = os.environ.get('HOUSECANARY_API_URL')
    HOUSECANARY_API_KEY = os.environ.get('HOUSECANARY_API_KEY')
    HOUSECANARY_API_SECRET = os.environ.get('HOUSECANARY_API_SECRET')

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.mailtrap.io')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 2525))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
