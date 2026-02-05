# Add the doctor command to the command registry
from .commands.doctor import run_health_check

def register_commands():
    # existing command registrations...
    command_registry['doctor'] = run_health_check