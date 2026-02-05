import os
import subprocess
import sys

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
        subprocess.run(["ping", "-c", "1", "google.com"], check=True, stdout=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def check_permissions():
    return os.access(os.getcwd(), os.W_OK)

def run_doctor():
    print("Running pyvm doctor...")
    pyenv_installed = check_pyenv()
    mise_installed = check_mise()
    network_ok = check_network()
    permissions_ok = check_permissions()

    if not pyenv_installed:
        print("Error: pyenv is not installed.")
    if not mise_installed:
        print("Error: mise is not installed.")
    if not network_ok:
        print("Error: Network is not reachable.")
    if not permissions_ok:
        print("Error: No write permissions in the current directory.")

    if pyenv_installed and mise_installed and network_ok and permissions_ok:
        print("All checks passed!")
    else:
        print("Please address the above issues.")