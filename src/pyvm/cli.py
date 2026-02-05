import click
from pyvm.utils import check_pyenv_installed, check_mise_installed, check_network, check_permissions

@click.group()
def cli():
    pass

@cli.command()
def doctor():
    """Run diagnostics to check your pyvm setup."""
    issues = []

    if not check_pyenv_installed():
        issues.append("pyenv is not installed.")
    if not check_mise_installed():
        issues.append("mise is not installed.")
    if not check_network():
        issues.append("Network is unreachable.")
    if not check_permissions():
        issues.append("Insufficient permissions for installation directory.")

    if issues:
        click.echo("Health check issues found:")
        for issue in issues:
            click.echo(f"- {issue}")
    else:
        click.echo("All checks passed. Your installation is healthy!")