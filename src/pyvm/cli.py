import os
import subprocess

class DoctorCommand:
    def run(self):
        self.check_pyenv()
        self.check_mise()
        self.check_network()
        self.check_permissions()

    def check_pyenv(self):
        if not self.is_tool_installed('pyenv'):
            print("pyenv is not installed.")
        else:
            print("pyenv is installed.")

    def check_mise(self):
        if not self.is_tool_installed('mise'):
            print("mise is not installed.")
        else:
            print("mise is installed.")

    def check_network(self):
        try:
            subprocess.check_output(['ping', '-c', '1', 'google.com'])
            print("Network is reachable.")
        except subprocess.CalledProcessError:
            print("Network is not reachable.")

    def check_permissions(self):
        if os.access('/', os.W_OK):
            print("Permissions are okay.")
        else:
            print("Permissions issue detected.")
    
    def is_tool_installed(self, tool):
        return subprocess.call(['which', tool], stdout=subprocess.PIPE) == 0