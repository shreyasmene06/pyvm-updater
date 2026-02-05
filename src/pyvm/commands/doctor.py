import os
import subprocess
import socket

def check_pyenv_installed():
    try:
        subprocess.run(["pyenv", "--version"], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_mise_installed():
    try:
        subprocess.run(["mise", "--version"], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_network_connection():
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        return False

def check_permissions():
    return os.access(os.getcwd(), os.W_OK)

def run_diagnostics():
    pyenv_installed = check_pyenv_installed()
    mise_installed = check_mise_installed()
    network_ok = check_network_connection()
    permissions_ok = check_permissions()

    return {
        "pyenv": pyenv_installed,
        "mise": mise_installed,
        "network": network_ok,
        "permissions": permissions_ok,
    }

def main():
    results = run_diagnostics()
    for key, value in results.items():
        status = "OK" if value else "FAIL"
        print(f"{key}: {status}")

if __name__ == "__main__":
    main()