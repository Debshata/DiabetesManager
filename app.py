import os
from dotenv import load_dotenv
load_dotenv(dotenv_path="APIKEY.env")
print("Gemini Key Loaded:", os.environ.get("GEMINI_API_KEY"))

import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the Base class
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "instance", "diabetes_manager.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure file uploads
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Configure Gemini API
app.config["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")

# Initialize the app with the extension
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return db.session.get(User, int(user_id))

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
