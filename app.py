"""
PDFForge Application Entry Point
"""
from pdfforge.create_app import create_app
from config import get_config
import os

# Get environment
env = os.environ.get('FLASK_ENV', 'development')

# Create app with appropriate config
app = create_app(get_config(env))

if __name__ == '__main__':
    # Get port from environment or default
    port = int(os.environ.get('PORT', 5000))

    print("\n" + "=" * 70)
    print("🔨 PDFFORGE - Professional PDF Tools")
    print("=" * 70)
    print(f"🚀 Environment: {env}")
    print(f"📱 Open your browser: http://localhost:{port}")
    print("✨ Modular Architecture | Professional PDF Processing")
    print("⏹️  Press Ctrl+C to stop")
    print("=" * 70 + "\n")

    # Run app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG']
    )