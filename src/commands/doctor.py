import subprocess
import socket
import os

def check_pyenv_mise():
    try:
        pyenv_installed = subprocess.run(['pyenv', '--version'], capture_output=True, text=True).returncode == 0
        mise_installed = subprocess.run(['mise', '--version'], capture_output=True, text=True).returncode == 0
        return pyenv_installed, mise_installed
    except FileNotFoundError:
        return False, False

def check_network():
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        return False

def check_permissions():
    return os.access(os.getcwd(), os.W_OK)

def run_diagnostics():
    pyenv, mise = check_pyenv_mise()
    network = check_network()
    permissions = check_permissions()

    print("Diagnostics:")
    print(f"pyenv installed: {'Yes' if pyenv else 'No'}")
    print(f"mise installed: {'Yes' if mise else 'No'}")
    print(f"Network reachable: {'Yes' if network else 'No'}")
    print(f"Write permissions: {'Yes' if permissions else 'No'}")

if __name__ == "__main__":
    run_diagnostics()