"""Flask application initialization"""

from flask import Flask
from config import Config


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register blueprints/routes
    from app import routes
    app.register_blueprint(routes.bp)

    return app