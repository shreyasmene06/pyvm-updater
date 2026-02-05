from .cli import DoctorCommand

# Register DoctorCommand in the command group
def register_commands(app):
    app.add_command(DoctorCommand(), name='doctor')