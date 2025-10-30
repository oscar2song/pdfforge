"""
Main Routes - Homepage and general routes
"""

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Render homepage"""
    return render_template("index.html")


@main_bp.route("/merge")
def merge_page():
    """Render merge tool page"""
    return render_template("merge.html")


@main_bp.route("/normalize")
def normalize_page():
    """Render normalize tool page"""
    return render_template("normalize.html")


@main_bp.route("/compress")
def compress_page():
    """Render compress tool page"""
    return render_template("compress.html")


@main_bp.route("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PDFForge"}