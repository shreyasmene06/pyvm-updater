import click
from .commands.doctor import run_diagnostics

@click.group()
def cli():
    """Python Version Manager CLI."""
    pass

@cli.command()
def doctor():
    """Run a health check on the pyvm installation."""
    run_diagnostics()

# Other existing commands...