#!/usr/bin/env python3
"""
Development setup script for PDFForge
"""
import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False


def main():
    print("🔨 PDFForge Development Setup")
    print("=" * 50)

    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("❌ Please activate your virtual environment first!")
        print("   On Windows: .venv\\Scripts\\activate")
        print("   On macOS/Linux: source .venv/bin/activate")
        sys.exit(1)

    # Upgrade pip
    run_command("python -m pip install --upgrade pip", "Upgrading pip")

    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("❌ Failed to install dependencies. Please check your requirements.txt")
        sys.exit(1)

    # Create necessary directories
    directories = ['tests/fixtures', 'static/css', 'static/js', 'static/images', 'logs']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

    # Create .env file if it doesn't exist
    if not Path('../.env').exists():
        with open('../.env.example', 'r') as example_file:
            env_content = example_file.read()
        with open('../.env', 'w') as env_file:
            env_file.write(env_content)
        print("✅ Created .env file from .env.example")

    # Verify installations
    print("\n🔍 Verifying installations...")

    tools = {
        'pytest': 'pytest --version',
        'black': 'black --version',
        'flake8': 'flake8 --version',
        'mypy': 'mypy --version'
    }

    for tool, command in tools.items():
        if run_command(command, f"Checking {tool}"):
            print(f"   ✅ {tool} is working")
        else:
            print(f"   ❌ {tool} is not working properly")

    print("\n🎉 Setup completed!")
    print("\n📝 Next steps:")
    print("   1. Run tests: pytest")
    print("   2. Format code: black pdfforge/ tests/")
    print("   3. Check types: mypy pdfforge/")
    print("   4. Start app: python app.py")


if __name__ == "__main__":
    main()
