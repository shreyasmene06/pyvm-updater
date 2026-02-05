import os
import subprocess
import requests

def check_pyenv():
    try:
        subprocess.run(["pyenv", "--version"], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_mise():
    try:
        subprocess.run(["mise", "--version"], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_network():
    try:
        response = requests.get("https://www.google.com", timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def check_permissions():
    return os.access(os.path.expanduser("~"), os.W_OK)

def run_doctor():
    checks = {
        "pyenv": check_pyenv(),
        "mise": check_mise(),
        "network": check_network(),
        "permissions": check_permissions(),
    }
    return checks