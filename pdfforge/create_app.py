"""
Flask Application Factory
UPDATED WITH TOC FEATURES
"""

import logging
import os

from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader, PrefixLoader


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

    # Attach external toc_generator templates if present
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        external_tmpl = os.path.join(project_root, "external", "toc_generator", "toc_generator", "templates")
        if os.path.isdir(external_tmpl):
            app.jinja_loader = ChoiceLoader([
                app.jinja_loader,
                PrefixLoader({
                    # Render premium templates with: render_template("premium/<name>.html")
                    "premium": FileSystemLoader(external_tmpl)
                }),
            ])
    except Exception:
        # Non-fatal if external templates are absent
        pass

    # Register blueprints
    register_blueprints(app)

    # Expose premium flag to templates
    @app.context_processor
    def inject_premium_flags():
        return {
            "premium_enabled": bool(app.config.get("WORD_PREMIUM_ENABLED", False))
        }

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
    from .routes.cleanup import cleanup_bp
    from .routes.compress import compress_bp
    from .routes.download import download_bp
    from .routes.main import main_bp
    from .routes.merge import merge_bp
    from .routes.normalize import normalize_bp

    # Premium Features (SaaS integration)
    from .routes.premium import premium_bp
    from .routes.split import split_bp

    # TOC Features (NEW)
    from .routes.toc import toc_bp
    from .routes.word import word_bp

    # Register existing blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(merge_bp)
    app.register_blueprint(normalize_bp)
    app.register_blueprint(compress_bp)
    app.register_blueprint(download_bp)
    app.register_blueprint(cleanup_bp)

    # Register TOC blueprints (NEW)
    app.register_blueprint(toc_bp)  # Standalone TOC Manager at /toc

    # Register Split blueprint (NEW)
    app.register_blueprint(split_bp)

    # Register Word blueprint (NEW)
    app.register_blueprint(word_bp)

    # Register Premium blueprint (SaaS) under /premium
    app.register_blueprint(premium_bp)


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
