import os
import subprocess
import requests

def check_pyenv_installed():
    try:
        subprocess.run(['pyenv', '--version'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def check_mise_installed():
    try:
        subprocess.run(['mise', '--version'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def check_network():
    try:
        response = requests.get('https://www.google.com', timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def check_permissions():
    return os.access(os.getcwd(), os.W_OK)

def run_health_check():
    pyenv_ok = check_pyenv_installed()
    mise_ok = check_mise_installed()
    network_ok = check_network()
    permissions_ok = check_permissions()

    print("Health Check Results:")
    print(f"pyenv installed: {'Yes' if pyenv_ok else 'No'}")
    print(f"mise installed: {'Yes' if mise_ok else 'No'}")
    print(f"Network reachable: {'Yes' if network_ok else 'No'}")
    print(f"Permissions OK: {'Yes' if permissions_ok else 'No'}")

if __name__ == "__main__":
    run_health_check()