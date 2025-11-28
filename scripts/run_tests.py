#!/usr/bin/env python3
"""
Test runner script for PDFForge
"""
import subprocess
import sys


def run_tests():
    """Run the test suite with coverage"""
    print("🧪 Running PDFForge Test Suite")
    print("=" * 50)

    commands = [
        ("pytest -v --cov=pdfforge --cov-report=html", "Running tests with coverage"),
        ("mypy pdfforge/", "Type checking"),
        ("black --check pdfforge/ tests/", "Code formatting check"),
        ("flake8 pdfforge/ tests/", "Code linting"),
    ]

    all_passed = True

    for command, description in commands:
        print(f"\n🔍 {description}...")
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print(f"✅ {description} passed")
        except subprocess.CalledProcessError as e:
            print(f"❌ {description} failed")
            print(f"   Error: {e.stderr}")
            all_passed = False

    if all_passed:
        print("\n🎉 All checks passed!")
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
