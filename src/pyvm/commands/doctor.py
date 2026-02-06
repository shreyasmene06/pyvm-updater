import subprocess
import requests
from ..utils import check_permissions

def check_pyenv():
    try:
        subprocess.run(['pyenv', '--version'], check=True)
        return True
    except FileNotFoundError:
        return False

def check_mise():
    try:
        subprocess.run(['mise', '--version'], check=True)
        return True
    except FileNotFoundError:
        return False

def check_network():
    try:
        response = requests.get("https://www.google.com", timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def doctor():
    print("Running pyvm doctor...")
    pyenv_installed = check_pyenv()
    mise_installed = check_mise()
    network_ok = check_network()
    permissions_ok = check_permissions()  # Assuming this function checks necessary permissions

    if pyenv_installed and mise_installed and network_ok and permissions_ok:
        print("All checks passed. Your environment is healthy!")
    else:
        print("Some checks failed. Please address the issues.")