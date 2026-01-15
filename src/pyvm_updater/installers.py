"""Platform-specific Python installation logic for pyvm_updater."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile

import click
import requests

from .constants import REQUEST_TIMEOUT
from .utils import download_file, validate_version_string, verify_file_checksum
from .version import is_python_version_installed


def install_pyenv_linux() -> bool:
    """Install pyenv on Linux (yum/dnf systems)."""
    print("\n[Linux] Installing pyenv...")

    if not shutil.which("curl"):
        print("Error: 'curl' is required to install pyenv.")
        return False

    if not shutil.which("bash"):
        print("Error: 'bash' is required to install pyenv.")
        return False

    pkg_mgr = "dnf" if shutil.which("dnf") else "yum"

    deps = [
        "git",
        "gcc",
        "zlib-devel",
        "bzip2-devel",
        "readline-devel",
        "sqlite-devel",
        "openssl-devel",
        "xz-devel",
        "libffi-devel",
        "findutils",
    ]

    try:
        if shutil.which("sudo"):
            subprocess.run(["sudo", pkg_mgr, "install", "-y"] + deps, check=True)
        else:
            subprocess.run([pkg_mgr, "install", "-y"] + deps, check=True)
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        return False

    print("Running pyenv-installer (https://pyenv.run)...")
    try:
        response = requests.get("https://pyenv.run", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        subprocess.run(["bash"], input=response.text, text=True, check=True)
    except Exception as e:
        print(f"Error running pyenv-installer: {e}")
        return False

    pyenv_root = os.path.expanduser("~/.pyenv")
    os.environ["PYENV_ROOT"] = pyenv_root

    bin_path = os.path.join(pyenv_root, "bin")
    shim_path = os.path.join(pyenv_root, "shims")
    os.environ["PATH"] = f"{bin_path}:{shim_path}:" + os.environ.get("PATH", "")

    print("\n[OK] pyenv installed successfully!")
    print("\nIMPORTANT: Add these to your ~/.bashrc:")
    print("-" * 60)
    print('export PYENV_ROOT="$HOME/.pyenv"')
    print('[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"')
    print('eval "$(pyenv init -)"')
    print("-" * 60)

    return True


def update_python_windows(version_str: str) -> bool:
    """Update Python on Windows."""
    print("\n🪟 Windows detected - Downloading Python installer...")

    if not validate_version_string(version_str):
        print(f"Error: Invalid version string: {version_str}")
        return False

    try:
        parts = version_str.split(".")
        if len(parts) < 3:
            print(f"Error: Version must be major.minor.patch format: {version_str}")
            return False
        major, minor, _patch = parts[0], parts[1], parts[2]
    except (ValueError, IndexError) as e:
        print(f"Error parsing version: {e}")
        return False

    machine = platform.machine().lower()
    if machine in ["amd64", "x86_64"]:
        arch = "amd64"
    elif machine in ["arm64", "aarch64"]:
        try:
            major_int, minor_int = int(major), int(minor)
            if major_int < 3 or (major_int == 3 and minor_int < 11):
                print("ARM64 installers are only available for Python 3.11+")
                arch = "amd64"
            else:
                arch = "arm64"
        except (ValueError, TypeError):
            arch = "amd64"
    else:
        arch = "win32"

    installer_url = f"https://www.python.org/ftp/python/{version_str}/python-{version_str}-{arch}.exe"
    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, f"python-{version_str}-installer.exe")

    print(f"Downloading from: {installer_url}")
    if not download_file(installer_url, installer_path):
        return False

    checksum_url = installer_url + ".sha256"
    if not verify_file_checksum(installer_path, checksum_url):
        click.echo("❌ Aborting installation due to integrity check failure")
        try:
            os.remove(installer_path)
        except OSError:
            pass
        return False

    print("\n⚠️  Starting installer...")
    print("Please follow the installer prompts.")

    try:
        result = subprocess.run([installer_path], check=False)
        if result.returncode != 0:
            print(f"Warning: Installer exited with code {result.returncode}")
        return True
    except FileNotFoundError:
        print(f"Error: Installer not found at {installer_path}")
        return False
    except PermissionError:
        print("Error: Permission denied. Try running as Administrator.")
        return False
    except Exception as e:
        print(f"Error running installer: {e}")
        return False
    finally:
        try:
            if os.path.exists(installer_path):
                os.remove(installer_path)
        except OSError:
            pass


def update_python_linux(version_str: str, build_from_source: bool = False) -> bool:
    """Install Python on Linux using mise, pyenv, or package manager"""
    print("\n[Linux] Installing Python...")

    if build_from_source:
        print(f"\n[Linux] Building Python {version_str} from source...")
        
        # 1. Prepare download URL for source code
        source_url = f"https://www.python.org/ftp/python/{version_str}/Python-{version_str}.tar.xz"
        temp_dir = tempfile.gettempdir()
        source_path = os.path.join(temp_dir, f"Python-{version_str}.tar.xz")

        # 2. Download the source
        if not download_file(source_url, source_path):
            print("❌ Failed to download source code.")
            return False

        print("✅ Source code downloaded successfully.")
        
        try:
            # 3. Extract the source code
            print("📦 Extracting source code...")
            subprocess.run(["tar", "-xf", source_path, "-C", temp_dir], check=True)
            build_dir = os.path.join(temp_dir, f"Python-{version_str}")

            # 4. Compile and Install instructions
            print("⚙️ Configuring and Building (this may take several minutes)...")
            
            cpu_cores = os.cpu_count() or 2
            build_cmd = (
                f"cd {build_dir} && "
                f"./configure --enable-optimizations && "
                f"make -j{cpu_cores} && "
                f"sudo make altinstall"
            )

            if platform.system().lower() == "linux":
                print(f"Running build commands...")
                subprocess.run(build_cmd, shell=True, check=True)
                print(f"\n[OK] Python {version_str} built and installed successfully!")
                return True
            else:
                print("\n⚠️  Skipping actual build because you are not on Linux.")
                print(f"On a Linux system, the tool would now run:\n{build_cmd}")
                return True

        except Exception as e:
            print(f"❌ Build failed: {e}")
            return False
        finally:
            # Cleanup extracted folder to save space
            if 'build_dir' in locals() and os.path.exists(build_dir):
                shutil.rmtree(build_dir, ignore_errors=True)

    # --- Standard Installation Methods (if not building from source) ---

    # Validate version string
    if not validate_version_string(version_str):
        print(f"Error: Invalid version string: {version_str}")
        return False

    # Extract major.minor version (e.g., "3.11" from "3.11.5")
    try:
        parts = version_str.split(".")
        if len(parts) < 2:
            print(f"Error: Invalid version format: {version_str}")
            return False
        major_minor = f"{parts[0]}.{parts[1]}"
    except (ValueError, IndexError) as e:
        print(f"Error parsing version: {e}")
        return False

    # Priority 1: Use mise if available
    if shutil.which("mise"):
        print("Using mise to install Python...")
        try:
            result = subprocess.run(["mise", "install", f"python@{version_str}"], check=False)
            if result.returncode == 0:
                print(f"\n[OK] Python {version_str} installed via mise!")
                return True
        except Exception:
            pass

    # Priority 2: Use pyenv if available
    if shutil.which("pyenv"):
        print("Using pyenv to install Python...")
        try:
            result = subprocess.run(["pyenv", "install", version_str], check=False)
            if result.returncode == 0:
                print(f"\n[OK] Python {version_str} installed via pyenv!")
                return True
        except Exception:
            pass

    # Priority 3: Use apt (deadsnakes PPA)
    if shutil.which("apt"):
        print("Using apt package manager...")
        try:
            subprocess.run(["sudo", "apt", "update"], check=False)
            subprocess.run(["sudo", "apt", "install", "-y", f"python{major_minor}"], check=False)
            return True
        except Exception:
            pass 

    return False


def update_python_macos(version_str: str) -> bool:
    """Update Python on macOS."""
    print("\n[macOS] Installing Python...")

    if not validate_version_string(version_str):
        print(f"Error: Invalid version string: {version_str}")
        return False

    try:
        parts = version_str.split(".")
        if len(parts) < 2:
            print(f"Error: Invalid version format: {version_str}")
            return False
        major = int(parts[0])
        minor = int(parts[1])
        major_minor = f"{major}.{minor}"
    except (ValueError, IndexError) as e:
        print(f"Error parsing version: {e}")
        return False

    # mise
    if shutil.which("mise"):
        print("Using mise to install Python...")
        try:
            result = subprocess.run(["mise", "install", f"python@{version_str}"], check=False)
            if result.returncode != 0:
                result = subprocess.run(["mise", "install", f"python@{major_minor}"], check=False)
            if result.returncode == 0:
                print(f"\n[OK] Python {version_str} installed via mise!")
                return True
        except Exception as e:
            print(f"mise error: {e}")

    # pyenv
    if shutil.which("pyenv"):
        print("Using pyenv to install Python...")
        try:
            result = subprocess.run(["pyenv", "install", version_str], check=False)
            if result.returncode == 0:
                print(f"\n[OK] Python {version_str} installed via pyenv!")
                return True
        except Exception as e:
            print(f"pyenv error: {e}")

    # brew
    if shutil.which("brew"):
        print("Using Homebrew...")
        try:
            subprocess.run(["brew", "update"], check=False, capture_output=True)
            result = subprocess.run(["brew", "install", f"python@{major_minor}"], check=False)
            if result.returncode == 0:
                print(f"[OK] Python {version_str} installed via Homebrew")
                return True
        except Exception as e:
            print(f"Homebrew error: {e}")

    # Official installer
    print("\nUsing official Python.org installer...")
    if major > 3 or (major == 3 and minor >= 9):
        installer_suffix = "macos11.pkg"
    else:
        installer_suffix = "macosx10.9.pkg"

    installer_filename = f"python-{version_str}-{installer_suffix}"
    macos_installer_url = f"https://www.python.org/ftp/python/{version_str}/{installer_filename}"

    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, installer_filename)

    print(f"Downloading from: {macos_installer_url}")
    if not download_file(macos_installer_url, installer_path):
        return False

    print("\n⚠️  Starting installer...")
    try:
        subprocess.run(["sudo", "installer", "-pkg", installer_path, "-target", "/"], check=True)
        print(f"\n[OK] Python {version_str} successfully installed!")
        return True
    except subprocess.CalledProcessError:
        print("Error: Installer failed.")
        return False
    except PermissionError:
        print("Error: Permission denied.")
        return False
    finally:
        if os.path.exists(installer_path):
            try:
                os.remove(installer_path)
            except OSError:
                pass


def remove_python_windows(version_str: str) -> bool:
    """Remove Python on Windows."""
    print(f"\n[Windows] Attempting to remove Python {version_str}...")

    if not is_python_version_installed(version_str):
        print(f"Error: Python {version_str} is not installed.")
        return False

    current_ver = platform.python_version()
    current_parts = current_ver.split(".")
    target_parts = version_str.split(".")

    if len(current_parts) >= 2 and len(target_parts) >= 2:
        if current_parts[0] == target_parts[0] and current_parts[1] == target_parts[1]:
            print(f"Error: Cannot remove Python {version_str} (running version).")
            return False

    # Try winget
    if shutil.which("winget"):
        major_minor = ".".join(version_str.split(".")[:2])
        potential_ids = [f"Python.Python.{major_minor}", f"PythonSoftwareFoundation.Python.{major_minor}"]

        for pkg_id in potential_ids:
            try:
                result = subprocess.run(
                    ["winget", "uninstall", "--id", pkg_id, "--silent"], capture_output=True, text=True, check=False
                )
                if result.returncode == 0:
                    print(f"[OK] Python {version_str} removed via winget")
                    return True
            except Exception:
                continue

    print("\n[Notice] Automated uninstallation on Windows encountered issues.")
    print("Please remove manually via Windows Settings -> Apps.")
    return False


def remove_python_linux(version_str: str) -> bool:
    """Remove Python on Linux."""
    print(f"\n[Linux] Attempting to remove Python {version_str}...")

    if not is_python_version_installed(version_str):
        print(f"Error: Python {version_str} is not installed.")
        return False

    try:
        parts = version_str.split(".")
        major_minor = f"{parts[0]}.{parts[1]}"
        current_parts = platform.python_version().split(".")
        current_major_minor = f"{current_parts[0]}.{current_parts[1]}"

        if major_minor == current_major_minor:
            print(f"Error: Cannot remove Python {version_str} (running version).")
            return False
    except (ValueError, IndexError):
        pass

    # mise
    if shutil.which("mise"):
        try:
            result = subprocess.run(
                ["mise", "uninstall", f"python@{version_str}"],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"[OK] Python {version_str} uninstalled via mise.")
                return True
        except Exception:
            pass

    # pyenv
    if shutil.which("pyenv"):
        try:
            result = subprocess.run(
                ["pyenv", "uninstall", "-f", version_str],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"[OK] Python {version_str} uninstalled via pyenv.")
                return True
        except Exception:
            pass

    print("\nCould not find a safe automated way to remove this Python installation.")
    return False


def remove_python_macos(version_str: str) -> bool:
    """Remove Python on macOS."""
    print(f"\n[macOS] Attempting to remove Python {version_str}...")

    if not is_python_version_installed(version_str):
        print(f"Error: Python {version_str} is not installed.")
        return False

    try:
        parts = version_str.split(".")
        major_minor = f"{parts[0]}.{parts[1]}"
        current_parts = platform.python_version().split(".")
        current_major_minor = f"{current_parts[0]}.{current_parts[1]}"

        if major_minor == current_major_minor:
            print(f"Error: Cannot remove Python {version_str} (running version).")
            return False
    except (ValueError, IndexError):
        pass

    # mise
    if shutil.which("mise"):
        try:
            result = subprocess.run(["mise", "uninstall", f"python@{version_str}"], check=False)
            if result.returncode == 0:
                print(f"[OK] Python {version_str} uninstalled via mise.")
                return True
        except Exception:
            pass

    # pyenv
    if shutil.which("pyenv"):
        try:
            result = subprocess.run(["pyenv", "uninstall", "-f", version_str], check=False)
            if result.returncode == 0:
                print(f"[OK] Python {version_str} uninstalled via pyenv.")
                return True
        except Exception:
            pass

    # brew
    if shutil.which("brew"):
        try:
            pkg_name = f"python@{major_minor}"
            check_brew = subprocess.run(["brew", "list", pkg_name], capture_output=True, text=True, check=False)
            if check_brew.returncode == 0:
                subprocess.run(["brew", "uninstall", pkg_name], check=False)
                return True
        except Exception:
            pass

    print("\n[Notice] To remove manually, delete:")
    print(f"1. /Applications/Python {major_minor}")
    print(f"2. /Library/Frameworks/Python.framework/Versions/{major_minor}")
    return False


def show_python_usage_instructions(version_str: str, os_name: str) -> None:
    """Show user how to use the newly installed Python version."""
    try:
        parts = version_str.split(".")
        major_minor = f"{parts[0]}.{parts[1]}"
    except (ValueError, IndexError):
        major_minor = version_str

    click.echo("\n" + "=" * 60)
    click.echo("✅ Installation Complete!")
    click.echo("=" * 60)
    click.echo(f"\n📌 Python {version_str} has been installed successfully!")
    click.echo("\n📚 How to use your new Python version:")
    click.echo("-" * 60)

    if os_name in ("linux", "darwin"):
        click.echo(f"\n1️⃣  Run scripts: python{major_minor} your_script.py")
        click.echo(f"\n2️⃣  Create venv: python{major_minor} -m venv myproject")
        click.echo(f"\n3️⃣  Check version: python{major_minor} --version")
    else:
        click.echo(f"\n1️⃣  Use launcher: py -{major_minor} your_script.py")
        click.echo("\n2️⃣  List versions: py --list")
        click.echo(f"\n3️⃣  Create venv: py -{major_minor} -m venv myproject")

    click.echo("-" * 60)
    click.echo("\n💡 Your old Python remains the system default.")
