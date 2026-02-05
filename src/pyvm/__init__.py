from .commands.doctor import run_doctor

def register_commands():
    # Existing command registrations
    register_command("doctor", run_doctor)