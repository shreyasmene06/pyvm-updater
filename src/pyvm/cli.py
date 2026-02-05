import subprocess
import sys
from .commands import Command

class DoctorCommand(Command):
    def run(self):
        self.check_pyenv()
        self.check_mise()
        self.check_network()
        self.check_permissions()

    def check_pyenv(self):
        try:
            subprocess.run(["pyenv", "--version"], check=True)
            print("✅ pyenv is installed.")
        except subprocess.CalledProcessError:
            print("❌ pyenv is not installed or not found in PATH.")

    def check_mise(self):
        try:
            subprocess.run(["mise", "--version"], check=True)
            print("✅ mise is installed.")
        except subprocess.CalledProcessError:
            print("❌ mise is not installed or not found in PATH.")

    def check_network(self):
        try:
            subprocess.run(["ping", "-c", "1", "google.com"], check=True)
            print("✅ Network is reachable.")
        except subprocess.CalledProcessError:
            print("❌ Network is not reachable.")

    def check_permissions(self):
        if os.access('/usr/local/bin', os.W_OK) or os.access('/usr/bin', os.W_OK):
            print("✅ Permissions are set correctly.")
        else:
            print("❌ Check your permissions for installation directories.")

# In the main application logic, register the DoctorCommand under the 'pyvm' command group.