"""
Flask Application Factory
"""

import logging
import os

from flask import Flask


def create_app(config_class=None):
    """
    Application factory function

    Args:
        config_class: Configuration class or object to use

    Returns:
        Flask app instance
    """
    # Get the base directory of the pdfforge package
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_folder = os.path.join(base_dir, "templates")
    static_folder = os.path.join(base_dir, "static")

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    # Handle both class and instance config
    if config_class:
        if hasattr(config_class, "__call__"):
            # It's a class, instantiate it
            app.config.from_object(config_class())
        else:
            # It's already an instance
            app.config.from_object(config_class)
    else:
        # Default config
        from config import DevelopmentConfig

        app.config.from_object(DevelopmentConfig())

    # Initialize extensions
    init_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Configure logging
    configure_logging(app)

    # Register error handlers
    register_error_handlers(app)

    return app


def init_extensions(app):
    """Initialize Flask extensions"""
    # Add extensions here (e.g., SQLAlchemy, Redis, etc.)


def register_blueprints(app):
    """Register Flask blueprints"""
    from .routes.compress import compress_bp
    from .routes.main import main_bp
    from .routes.merge import merge_bp
    from .routes.normalize import normalize_bp
    from .routes.download import download_bp  # Add this import

    app.register_blueprint(main_bp)
    app.register_blueprint(merge_bp)
    app.register_blueprint(normalize_bp)
    app.register_blueprint(compress_bp)
    app.register_blueprint(download_bp)  # Add this registration


def configure_logging(app):
    """Configure application logging"""
    if not app.debug:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception("Internal error")
        return {"error": "Internal server error"}, 500
