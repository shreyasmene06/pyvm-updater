from .commands.doctor import run_diagnostics

def register_commands(app):
    app.add_command("doctor", run_diagnostics)
    # other command registrations...