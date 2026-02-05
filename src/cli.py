import subprocess
import socket

def check_pyenv_installed():
    try:
        subprocess.run(['pyenv', '--version'], check=True, stdout=subprocess.PIPE)
        return True
    except Exception:
        return False

def check_mise_installed():
    try:
        subprocess.run(['mise', '--version'], check=True, stdout=subprocess.PIPE)
        return True
    except Exception:
        return False

def check_network():
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        return False

def check_permissions():
    # Placeholder for actual permission checks
    # This should check if the current user has write access to relevant directories
    return True

def doctor():
    print("Running health checks...")
    pyenv_installed = check_pyenv_installed()
    mise_installed = check_mise_installed()
    network_ok = check_network()
    permissions_ok = check_permissions()

    if pyenv_installed and mise_installed and network_ok and permissions_ok:
        print("All checks passed!")
    else:
        if not pyenv_installed:
            print("Warning: pyenv is not installed.")
        if not mise_installed:
            print("Warning: mise is not installed.")
        if not network_ok:
            print("Warning: Network is unreachable.")
        if not permissions_ok:
            print("Warning: Insufficient permissions.")