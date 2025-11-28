#!/usr/bin/env python3
"""
Auto-format all Python files with black and isort (120 char line length)
"""
import subprocess
import sys


def format_code():
    """Format all code with black and isort"""
    print("🔧 PDFForge - Auto-formatting Code (120 char line length)")
    print("=" * 60)

    commands = [
        ("Running isort to sort imports...", "python -m isort --profile black --line-length 120 src/pdfforge/ tests/"),
        ("Running black to format code...", "python -m black --line-length 120 src/pdfforge/ tests/"),
    ]

    for description, command in commands:
        print(f"\n📋 {description}")
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print("   ✅ COMPLETED")
            if result.stdout:
                print(f"   {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print("   ❌ FAILED")
            if e.stderr:
                print(f"   Error: {e.stderr.strip()}")
            if e.stdout:
                print(f"   Output: {e.stdout.strip()}")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("✨ All files have been formatted! ✨")
    print("\n💡 Next steps:")
    print("   1. Review the changes with: git diff")
    print("   2. Run quality checks: python run_quality_checks.py")
    print("   3. Commit the formatted code")


if __name__ == "__main__":
    format_code()
