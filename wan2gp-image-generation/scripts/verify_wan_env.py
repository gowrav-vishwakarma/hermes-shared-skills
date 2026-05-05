#!/usr/bin/env python3
"""
WanGP Environment Verification Script
Checks that the WanGP Python environment is correctly configured.

Run this before any WanGP CLI commands to ensure:
- Correct Python interpreter
- PyTorch is installed
- WanGP app directory is correct
- Required dependencies are available
"""

import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(SCRIPT_DIR))
try:
    from _env import required  # type: ignore
finally:
    try:
        sys.path.remove(str(SCRIPT_DIR))
    except ValueError:
        pass

WAN_APP_DIR = str(required("WAN_APP_DIR"))
ENV_PYTHON = os.environ.get("WAN_PYTHON") or os.path.join(WAN_APP_DIR, "env", "bin", "python")


def check_python():
    """Check if we're using the correct Python interpreter."""
    print(f"Python interpreter: {sys.executable}")
    print(f"Expected: {ENV_PYTHON}")

    if sys.executable == ENV_PYTHON:
        print("OK using correct WanGP Python interpreter")
        return True
    else:
        print("FAIL not using WanGP Python interpreter!")
        print(f"  Run: {ENV_PYTHON} -c 'import torch'")
        return False


def check_torch():
    """Check if PyTorch is installed and accessible."""
    try:
        import torch
        print(f"OK PyTorch version: {torch.__version__}")

        if torch.cuda.is_available():
            print(f"OK CUDA available: {torch.cuda.get_device_name(0)}")
        else:
            print("FAIL CUDA NOT available")
        return True
    except ImportError:
        print("FAIL PyTorch not installed in this environment!")
        return False


def check_wan_app():
    """Check if we're in the correct WanGP app directory."""
    if os.getcwd() == WAN_APP_DIR:
        print(f"OK in correct WanGP directory: {WAN_APP_DIR}")
        return True
    else:
        print(f"FAIL not in WanGP directory!")
        print(f"  Expected: {WAN_APP_DIR}")
        print(f"  Current: {os.getcwd()}")
        print(f"  Run: cd {WAN_APP_DIR}")
        return False


def check_dependencies():
    """Check for common WanGP dependencies."""
    missing = []

    try:
        import PIL.Image  # noqa: F401
    except ImportError:
        missing.append("Pillow (PIL)")

    try:
        import torchvision  # noqa: F401
    except ImportError:
        missing.append("torchvision")

    try:
        import transformers  # noqa: F401
    except ImportError:
        missing.append("transformers")

    if missing:
        print(f"FAIL missing dependencies: {', '.join(missing)}")
        return False
    else:
        print("OK all common dependencies available")
        return True


def main():
    print("=" * 60)
    print("WanGP Environment Verification")
    print("=" * 60)
    print()

    checks = [
        ("Python interpreter", check_python),
        ("PyTorch", check_torch),
        ("WanGP directory", check_wan_app),
        ("Dependencies", check_dependencies),
    ]

    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        result = check_func()
        results.append(result)

    print("\n" + "=" * 60)
    if all(results):
        print("OK all checks passed; WanGP environment is ready.")
        sys.exit(0)
    else:
        print("FAIL some checks failed; see above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
