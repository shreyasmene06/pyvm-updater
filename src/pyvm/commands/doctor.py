import subprocess
import os

def check_pyenv():
    try:
        result = subprocess.run(['pyenv', 'versions'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_mise():
    try:
        result = subprocess.run(['mise', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_network():
    try:
        result = subprocess.run(['ping', '-c', '1', 'google.com'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def check_permissions(path):
    return os.access(path, os.W_OK)

def run_doctor():
    pyenv_installed = check_pyenv()
    mise_installed = check_mise()
    network_ok = check_network()
    permissions_ok = check_permissions('/path/to/install/dir')

    print("Health Check Results:")
    print(f"pyenv installed: {'Yes' if pyenv_installed else 'No'}")
    print(f"mise installed: {'Yes' if mise_installed else 'No'}")
    print(f"Network reachable: {'Yes' if network_ok else 'No'}")
    print(f"Permissions OK: {'Yes' if permissions_ok else 'No'}")