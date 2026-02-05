import subprocess
import requests
import os

def check_pyenv_installed():
    try:
        subprocess.run(["pyenv", "--version"], check=True)
        return True
    except Exception:
        return False

def check_mise_installed():
    try:
        subprocess.run(["mise", "--version"], check=True)
        return True
    except Exception:
        return False

def check_network_reachable():
    try:
        response = requests.get("https://www.python.org", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def check_permissions():
    return os.access(os.path.expanduser("~/.pyenv"), os.W_OK)

def run_diagnostics():
    print("Running diagnostics...")
    pyenv_ok = check_pyenv_installed()
    mise_ok = check_mise_installed()
    network_ok = check_network_reachable()
    permissions_ok = check_permissions()

    print(f"pyenv installed: {'Yes' if pyenv_ok else 'No'}")
    print(f"mise installed: {'Yes' if mise_ok else 'No'}")
    print(f"Network reachable: {'Yes' if network_ok else 'No'}")
    print(f"Permissions ok: {'Yes' if permissions_ok else 'No'}")

    if pyenv_ok and mise_ok and network_ok and permissions_ok:
        print("All checks passed!")
    else:
        print("Some checks failed. Please review the output.")