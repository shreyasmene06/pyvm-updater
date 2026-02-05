import click
import os
import subprocess

@click.command()
def doctor():
    """Run a health check on your pyvm setup."""
    click.echo("Checking for pyenv/mise installation...")
    if subprocess.run(["which", "pyenv"], stdout=subprocess.PIPE).returncode != 0:
        click.echo("Error: pyenv not found. Please install it.")
    elif subprocess.run(["which", "mise"], stdout=subprocess.PIPE).returncode != 0:
        click.echo("Error: mise not found. Please install it.")
    else:
        click.echo("pyenv and mise are installed.")

    click.echo("Checking network connectivity...")
    try:
        subprocess.run(["ping", "-c", "1", "google.com"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        click.echo("Network is reachable.")
    except Exception:
        click.echo("Error: Network is not reachable.")

    click.echo("Checking permissions...")
    if os.access('/usr/local/bin', os.W_OK):
        click.echo("Permissions are fine.")
    else:
        click.echo("Error: Insufficient permissions for /usr/local/bin.")