from flask import Flask
from dotenv import load_dotenv
import logging
import sys

from app.config import Config
from app.extensions import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Load environment variables
load_dotenv()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes import register_blueprints
    register_blueprints(app)

    # Create tables
    with app.app_context():
        db.create_all()
        app.logger.info("✅ Database tables created/verified")

    app.logger.info("🚀 Application started successfully")
    return app