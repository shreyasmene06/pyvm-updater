import subprocess
import os

def check_pyenv():
    try:
        subprocess.run(["pyenv", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def check_mise():
    try:
        subprocess.run(["mise", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def check_network():
    try:
        response = subprocess.run(["ping", "-c", "1", "google.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def check_permissions():
    # Check if the user has write access to the installation directories
    return os.access(os.path.expanduser("~/.config/pyvm"), os.W_OK)

def run_diagnostics():
    pyenv_installed = check_pyenv()
    mise_installed = check_mise()
    network_ok = check_network()
    permissions_ok = check_permissions()

    print("Diagnostics Report:")
    print(f"pyenv installed: {'Yes' if pyenv_installed else 'No'}")
    print(f"mise installed: {'Yes' if mise_installed else 'No'}")
    print(f"Network reachable: {'Yes' if network_ok else 'No'}")
    print(f"Permissions OK: {'Yes' if permissions_ok else 'No'}")

    if not (pyenv_installed and mise_installed and network_ok and permissions_ok):
        print("Warning: Please resolve the issues above.")