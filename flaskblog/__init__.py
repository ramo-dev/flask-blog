# __init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO, emit
from flask_migrate import Migrate, upgrade
import os

app = Flask(__name__)

socketio = SocketIO(app)

app.config['SECRET_KEY'] = 'd1272661fd1b7bc6b5971bda2a5a00a4'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)

migrate = Migrate(app, db)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'noreplyfbtest@gmail.com'
app.config['MAIL_PASSWORD'] = 'lkosbolnuhnjfgxc'

mail = Mail(app)

from flaskblog import routes

