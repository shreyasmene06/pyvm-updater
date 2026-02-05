import subprocess
import socket
import os

def check_pyenv_installed():
    try:
        result = subprocess.run(['pyenv', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_mise_installed():
    try:
        result = subprocess.run(['mise', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_network():
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        return False

def check_permissions():
    return os.access(os.getcwd(), os.W_OK)

def run_diagnostics():
    print("Running diagnostics...")
    pyenv_status = "OK" if check_pyenv_installed() else "NOT INSTALLED"
    mise_status = "OK" if check_mise_installed() else "NOT INSTALLED"
    network_status = "OK" if check_network() else "NOT REACHABLE"
    permissions_status = "OK" if check_permissions() else "NO WRITE PERMISSION"

    print(f"pyenv: {pyenv_status}")
    print(f"mise: {mise_status}")
    print(f"Network: {network_status}")
    print(f"Permissions: {permissions_status}")