import os
import subprocess
import sys

def check_pyenv_installed():
    """Check if pyenv is installed."""
    try:
        subprocess.run(['pyenv', '--version'], check=True, stdout=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_mise_installed():
    """Check if mise is installed."""
    try:
        subprocess.run(['mise', '--version'], check=True, stdout=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_network():
    """Check if we can reach a known server."""
    try:
        subprocess.run(['ping', '-c', '1', 'example.com'], check=True, stdout=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def check_permissions():
    """Check if we have write permissions to necessary directories."""
    try:
        with open(os.path.join(os.path.expanduser('~'), 'pyvm_test.tmp'), 'w') as f:
            f.write('test')
        os.remove(os.path.join(os.path.expanduser('~'), 'pyvm_test.tmp'))
        return True
    except Exception:
        return False

def run_diagnostics():
    """Run all diagnostics and print results."""
    print("Running pyvm doctor...")
    print("Checking pyenv installation...")
    if check_pyenv_installed():
        print("pyenv is installed.")
    else:
        print("pyenv is NOT installed.")

    print("Checking mise installation...")
    if check_mise_installed():
        print("mise is installed.")
    else:
        print("mise is NOT installed.")

    print("Checking network access...")
    if check_network():
        print("Network is reachable.")
    else:
        print("Network is NOT reachable.")

    print("Checking permissions...")
    if check_permissions():
        print("Permissions are correct.")
    else:
        print("Permissions are NOT correct.")

if __name__ == "__main__":
    run_diagnostics()