from .commands.doctor import run_diagnostics

def main():
    # Existing command registration code
    # ...
    command_registry["doctor"] = run_diagnostics