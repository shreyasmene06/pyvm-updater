from .commands.doctor import main as doctor_main

# Add to command registry
COMMANDS['doctor'] = doctor_main