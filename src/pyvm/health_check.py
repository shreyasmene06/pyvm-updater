import subprocess
import socket

def check_pyenv_installed():
    try:
        subprocess.run(['pyenv', '--version'], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("pyenv is not installed.")

def check_mise_installed():
    try:
        subprocess.run(['mise', '--version'], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("mise is not installed.")

def check_network():
    try:
        socket.create_connection(("www.google.com", 80))
        print("Network is reachable.")
    except OSError:
        print("Network is not reachable.")

def check_permissions():
    if os.access('/usr/local/bin', os.W_OK):
        print("Permissions are okay.")
    else:
        print("Permission issues detected.")

def run_health_checks():
    check_pyenv_installed()
    check_mise_installed()
    check_network()
    check_permissions()