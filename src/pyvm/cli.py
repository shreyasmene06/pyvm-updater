import click
from .check_requirements import check_pyenv_mise, check_network, check_permissions

@click.group()
def cli():
    pass

@cli.command()
def doctor():
    """Run health checks for the pyvm environment."""
    check_pyenv_mise()
    check_network()
    check_permissions()