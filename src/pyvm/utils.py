import os
import subprocess

def check_pyenv_installed():
    """Check if pyenv is installed."""
    result = subprocess.run(["pyenv", "--version"], capture_output=True)
    return result.returncode == 0

def check_mise_installed():
    """Check if mise is installed."""
    result = subprocess.run(["mise", "--version"], capture_output=True)
    return result.returncode == 0

def check_network():
    """Check network connectivity."""
    try:
        response = subprocess.run(["ping", "-c", "1", "google.com"], capture_output=True)
        return response.returncode == 0
    except Exception:
        return False

def check_permissions():
    """Check permissions for installation directory."""
    install_dir = os.path.expanduser("~/.pyvm")
    return os.access(install_dir, os.W_OK)