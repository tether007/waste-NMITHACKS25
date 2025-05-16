import os
import logging
import sys

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Configure more detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
bcrypt = Bcrypt()

# Create the app
app = Flask(__name__,static_folder='static')
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure the database with better error handling
try:
    # Default to PostgreSQL for local development if DATABASE_URL not set
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        logging.warning("DATABASE_URL not found in environment. Using SQLite as fallback.")
        database_url = "sqlite:///waste_management.db"
        
    # Fix for Render PostgreSQL URLs (postgres:// vs postgresql://)
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        logging.info("Updated database URL prefix from postgres:// to postgresql://")
    
    # Configure SQLAlchemy
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,  # Reconnect after 5 minutes of inactivity
        "pool_pre_ping": True,  # Verify connections before using them
        "pool_size": 10,  # Maximum number of connections to keep
        "max_overflow": 20,  # Maximum number of connections to create beyond pool_size
    }
    
    # For PostgreSQL connections, add a timeout
    if database_url.startswith("postgresql://"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"]["connect_args"] = {
            "connect_timeout": 30,  # 30 seconds timeout for connections
        }
        
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Log database connection info (without exposing credentials)
    db_type = database_url.split("://")[0]
    logging.info(f"Connecting to database: {db_type}://*****@*****")
except Exception as e:
    logging.error(f"Database configuration error: {str(e)}")
    # Fallback to SQLite if there's a configuration error
    database_url = "sqlite:///waste_management.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    logging.warning(f"Using fallback SQLite database: {database_url}")

# Configure upload folder
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize the extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
bcrypt.init_app(app)

# Set up the user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))


with app.app_context():
    try:
        import models  # import your models first
        db.create_all()
        logging.info("Database tables created successfully.")
    except Exception as e:
        logging.error(f"Error creating database tables: {str(e)}")
