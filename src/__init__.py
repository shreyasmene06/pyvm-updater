from .commands.doctor import run_diagnostics

def main():
    # Existing command registration logic
    # Add command registration for `pyvm doctor`
    cli.add_command("doctor", run_diagnostics)