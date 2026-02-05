import click
import os
import subprocess

@click.command()
def doctor():
    """Run a health check on pyvm."""
    
    # Check if pyenv is installed
    if not is_pyenv_installed():
        click.echo("pyenv is not installed. Please install pyenv.")
        return

    # Check if mise is installed
    if not is_mise_installed():
        click.echo("mise is not installed. Please install mise.")
        return

    # Check network connectivity
    if not is_network_reachable():
        click.echo("Network is not reachable. Check your connection.")
        return

    # Check permissions
    if not has_correct_permissions():
        click.echo("Permissions are not set correctly. Check your installation.")
        return

    click.echo("All checks passed! Your installation is healthy.")

def is_pyenv_installed():
    return subprocess.call(['pyenv', '--version'], stdout=subprocess.DEVNULL) == 0

def is_mise_installed():
    return subprocess.call(['mise', '--version'], stdout=subprocess.DEVNULL) == 0

def is_network_reachable():
    return subprocess.call(['ping', '-c', '1', 'google.com'], stdout=subprocess.DEVNULL) == 0

def has_correct_permissions():
    # Check permissions for critical directories
    return os.access('/usr/local/bin', os.X_OK) and os.access('/usr/bin', os.X_OK)