from flask import Flask
from app.db import init_app
from config import Config
from flask_login import LoginManager

# Start Flask app
app = Flask(__name__)

# Load variables from the config file
app.config.from_object(Config)

# Set up the database functionality
init_app(app)

# User logins
login_manager = LoginManager()
login_manager.init_app(app)
# Go to this route if a user tries to access a "login-required" page
login_manager.login_view = "login"

from app import routes
