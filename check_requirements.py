#!/usr/bin/env python3
"""
Pre-installation checker for Python Version Manager
Verifies system requirements and dependencies before installation
"""

import platform
import subprocess
import sys
from typing import Dict


def check_python_version() -> bool:
    """Check if Python version meets minimum requirements"""
    print("✓ Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro} (minimum 3.7 required)")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor}.{version.micro} is too old!")
        print("    Please upgrade to Python 3.7 or higher")
        return False


def check_pip() -> bool:
    """Check if pip is installed"""
    print("✓ Checking pip...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True, check=True)
        print(f"  ✓ pip is installed: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("  ✗ pip is not installed!")
        print("    Install with: python -m ensurepip --upgrade")
        return False
    except Exception as e:
        print(f"  ✗ Error checking pip: {e}")
        return False


def check_internet() -> bool:
    """Check basic internet connectivity"""
    print("✓ Checking internet connectivity...")
    try:
        import socket

        socket.create_connection(("www.python.org", 443), timeout=5)
        print("  ✓ Internet connection OK")
        return True
    except OSError:
        print("  ⚠ Cannot reach python.org")
        print("    Internet connection may be required for updates")
        return False


def check_existing_dependencies() -> Dict[str, bool]:
    """Check if required packages are already installed"""
    print("✓ Checking existing dependencies...")
    packages :dict[str, bool] = {
        "requests": False,
        "beautifulsoup4": False,
        "packaging": False,
        "click": False
    }

    for package in packages:
        try:
            __import__(package if package != "beautifulsoup4" else "bs4")
            print(f"  ✓ {package} already installed")
            packages[package] = True
        except ImportError:
            print(f"  ○ {package} will be installed")
            packages[package] = False

    return packages


def check_permissions() -> bool:
    """Check if user has permission to install packages"""
    print("✓ Checking installation permissions...")

    # Try to check site-packages location
    try:
        import site

        site_packages = site.getsitepackages()
        print(f"  ○ Will install to: {site_packages[0] if site_packages else 'default location'}")

        # On Unix systems, check if we need sudo
        if platform.system().lower() in ["linux", "darwin"]:
            import os

            if not os.access(site_packages[0] if site_packages else "/usr/local", os.W_OK):
                print("  ⚠ May require sudo for system-wide installation")
                print("    Consider using: pip install --user")
                return False

        return True
    except Exception as e:
        print(f"  ⚠ Could not check permissions: {e}")
        return True


def check_os_support() -> bool:
    """Check if OS is supported"""
    print("✓ Checking operating system...")
    os_name = platform.system()

    if os_name == "Windows":
        print(f"  ✓ Windows detected: {platform.release()}")
        return True
    elif os_name == "Linux":
        print(f"  ✓ Linux detected: {platform.release()}")
        # Check for package managers
        import shutil

        if shutil.which("apt"):
            print("    - apt package manager found")
        elif shutil.which("dnf"):
            print("    - dnf package manager found")
        elif shutil.which("yum"):
            print("    - yum package manager found")
        else:
            print("    ⚠ No supported package manager found")
        return True
    elif os_name == "Darwin":
        print(f"  ✓ macOS detected: {platform.mac_ver()[0]}")
        import shutil

        if shutil.which("brew"):
            print("    - Homebrew found")
        else:
            print("    ⚠ Homebrew not found (recommended for easy updates)")
        return True
    else:
        print(f"  ⚠ Unsupported OS: {os_name}")
        return False


def main() -> int:
    """Run all checks"""
    print("=" * 60)
    print("  Python Version Manager - Pre-Installation Check")
    print("=" * 60)
    print()

    checks : Dict[str, bool]= {
        "Python version": check_python_version(),
        "pip": check_pip(),
        "Internet": check_internet(),
        "OS support": check_os_support(),
        "Permissions": check_permissions(),
    }

    # Check dependencies (informational only)
    packages = check_existing_dependencies()

    print()
    print("=" * 60)
    print("  Summary")
    print("=" * 60)

    critical_checks = ["Python version", "pip", "OS support"]
    all_critical_passed = all(checks[check] for check in critical_checks if check in checks)

    if all_critical_passed:
        print("✓ All critical checks passed!")
        print()
        print("Ready to install. Run:")
        print("  pip install -e .")
        print()
        print("Or for user-only installation:")
        print("  pip install --user -e .")
        print()

        missing_packages = [pkg for pkg, installed in packages.items() if not installed]
        if missing_packages:
            print("The following packages will be installed automatically:")
            for pkg in missing_packages:
                print(f"  - {pkg}")

        return 0
    else:
        print("✗ Some critical checks failed!")
        print()
        print("Please fix the issues above before installing.")

        failed = [check for check, passed in checks.items() if not passed and check in critical_checks]
        if failed:
            print("\nFailed checks:")
            for check in failed:
                print(f"  - {check}")

        return 1


if __name__ == "__main__":
    sys.exit(main())
