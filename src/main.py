import cli

def main():
    # Existing command handling logic
    command = parse_command_line()
    if command == "doctor":
        cli.doctor()
    else:
        # Existing command handling