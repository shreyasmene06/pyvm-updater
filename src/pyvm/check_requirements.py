import os
import subprocess
import sys

def check_pyenv_mise():
    """Check if pyenv and mise are installed."""
    if not (is_tool_installed('pyenv') and is_tool_installed('mise')):
        print("Error: pyenv and/or mise are not installed.")
        sys.exit(1)

def check_network():
    """Check network connectivity."""
    try:
        subprocess.check_call(['ping', '-c', '1', '8.8.8.8'], stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Error: Network is unreachable.")
        sys.exit(1)

def check_permissions():
    """Check if the user has the necessary permissions."""
    if not os.access('/usr/local/bin', os.W_OK):
        print("Error: Insufficient permissions to install Python versions.")
        sys.exit(1)

def is_tool_installed(tool):
    """Check if a tool is installed."""
    return subprocess.call(['which', tool], stdout=subprocess.DEVNULL) == 0