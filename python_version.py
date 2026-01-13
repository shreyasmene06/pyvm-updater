#!/usr/bin/env python3
"""
Python Version Manager - CLI Tool
Checks and installs Python to the latest version across Windows, Linux, and macOS

IMPORTANT: This tool installs Python but does NOT modify your system's default Python.
Your existing Python installation remains unchanged to avoid breaking system tools.

Requirements:
    pip install requests beautifulsoup4 packaging click

Note: Dependencies are automatically installed via setup.py during CLI installation.
"""

import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Optional, Tuple, List, Dict

try:
    import click
    import requests
    from bs4 import BeautifulSoup
    from packaging import version as pkg_version
except ImportError as e:
    print("ERROR: Missing required packages.")
    print("Please install them using:")
    print("  pip install requests beautifulsoup4 packaging click")
    print("\nOr install this tool via:")
    print("  pip install -e .")
    print(f"\nDetails: {e}")
    sys.exit(1)

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
DOWNLOAD_TIMEOUT = 120  # seconds
REQUEST_TIMEOUT = 15  # seconds


def get_os_info():
    """Detect the operating system and architecture"""
    os_name = platform.system().lower()
    machine = platform.machine().lower()

    # Normalize architecture names
    if machine in ["amd64", "x86_64"]:
        arch = "amd64"
    elif machine in ["arm64", "aarch64"]:
        arch = "arm64"
    else:
        arch = "x86"

    return os_name, arch


def is_admin():
    """Check if script is running with admin/sudo privileges"""
    try:
        if platform.system().lower() == "windows":
            import ctypes

            # Type hint fix: windll is only available on Windows
            return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore[attr-defined]
        else:
            # os.geteuid() only exists on Unix-like systems
            return hasattr(os, "geteuid") and os.geteuid() == 0
    except Exception:
        return False


def validate_version_string(version_str: str) -> bool:
    """Validate that version string matches expected format (e.g., 3.11.5)"""
    if not version_str:
        return False
    # Match format: digit.digit[.digit[...]]
    pattern = r"^\d+\.\d+(\.\d+)*$"
    return bool(re.match(pattern, version_str))


def get_installed_python_versions() -> list[dict]:
    """Detect Python versions installed on the system"""
    versions = []
    os_name, _ = get_os_info()
    found = set()  # Track versions we've already found

    if os_name == "windows":
        # Use py launcher to list versions
        try:
            result = subprocess.run(["py", "--list"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    # Format: " -V:3.12 *" or " -3.12-64"
                    line = line.strip()
                    match = re.search(r'-(?:V:)?(\d+\.\d+)', line)
                    if match:
                        ver = match.group(1)
                        is_default = "*" in line
                        if ver not in found:
                            found.add(ver)
                            versions.append({"version": ver, "path": None, "default": is_default})
        except FileNotFoundError:
            pass
    else:
        # Unix-like: search multiple sources

        # 1. Check mise installed versions
        mise_python_dir = os.path.expanduser("~/.local/share/mise/installs/python")
        if os.path.isdir(mise_python_dir):
            try:
                for entry in os.listdir(mise_python_dir):
                    if re.match(r"^\d+\.\d+", entry):
                        ver = entry
                        if ver not in found:
                            full_path = os.path.join(mise_python_dir, entry, "bin", "python3")
                            if os.path.exists(full_path):
                                found.add(ver)
                                versions.append(
                                    {
                                        "version": ver,
                                        "path": full_path,
                                        "default": full_path == sys.executable
                                        or sys.executable.startswith(os.path.join(mise_python_dir, entry)),
                                    }
                                )
            except PermissionError:
                pass

        # 2. Check pyenv installed versions
        pyenv_root = os.environ.get("PYENV_ROOT", os.path.expanduser("~/.pyenv"))
        pyenv_versions_dir = os.path.join(pyenv_root, "versions")
        if os.path.isdir(pyenv_versions_dir):
            try:
                for entry in os.listdir(pyenv_versions_dir):
                    if re.match(r"^\d+\.\d+", entry):
                        ver = entry
                        if ver not in found:
                            full_path = os.path.join(pyenv_versions_dir, entry, "bin", "python3")
                            if os.path.exists(full_path):
                                found.add(ver)
                                versions.append(
                                    {"version": ver, "path": full_path, "default": full_path == sys.executable}
                                )
            except PermissionError:
                pass

        # 3. Check system paths for python executables
        search_paths = ["/usr/bin", "/usr/local/bin", "/opt/homebrew/bin", os.path.expanduser("~/.local/bin")]

        for path in search_paths:
            if os.path.isdir(path):
                try:
                    for entry in os.listdir(path):
                        match = re.match(r"^python(\d+\.\d+)$", entry)
                        if match:
                            ver = match.group(1)
                            if ver not in found:
                                found.add(ver)
                                full_path = os.path.join(path, entry)
                                # Check if it's actually executable
                                if os.access(full_path, os.X_OK):
                                    # Get full version
                                    try:
                                        result = subprocess.run(
                                            [full_path, "--version"],
                                            capture_output=True,
                                            text=True,
                                            check=False,
                                            timeout=5,
                                        )
                                        if result.returncode == 0:
                                            full_ver = result.stdout.strip().replace("Python ", "")
                                            versions.append(
                                                {
                                                    "version": full_ver,
                                                    "path": full_path,
                                                    "default": full_path == sys.executable,
                                                }
                                            )
                                    except Exception:
                                        versions.append({"version": ver, "path": full_path, "default": False})
                except PermissionError:
                    pass

    # Sort by version descending
    def version_key(x):
        try:
            return [int(p) for p in x["version"].split(".")[:3]]
        except ValueError:
            return [0, 0, 0]

    versions.sort(key=version_key, reverse=True)

    # Ensure current Python is in the list
    current_ver = platform.python_version()
    found_current = any(v["version"] == current_ver for v in versions)

    if not found_current:
        versions.insert(0, {"version": current_ver, "path": sys.executable, "default": True})
    else:
        # Mark current Python as default
        for v in versions:
            if v["version"] == current_ver:
                v["default"] = True
                break

    return versions


def get_latest_python_info_with_retry() -> tuple[Optional[str], Optional[str]]:
    """Fetch the latest Python version with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            result = get_latest_python_info()
            if result[0]:  # If we got a version
                return result
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                print(f"All retry attempts failed: {e}")
    return None, None


def get_latest_python_info() -> tuple[Optional[str], Optional[str]]:
    """Fetch the latest Python version and download URLs"""
    URL = "https://www.python.org/downloads/"

    try:
        response = requests.get(URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        # Specify parser explicitly for consistency
        soup = BeautifulSoup(response.text, "html.parser")

        # Get version from download button
        download_button = soup.find("a", class_="button")
        if not download_button:
            print("Error: Could not find download button on Python.org")
            return None, None

        latest_ver_string = download_button.get_text(strip=True)
        latest_ver = latest_ver_string.split()[-1]

        # Validate version string
        if not validate_version_string(latest_ver):
            print(f"Error: Invalid version format retrieved: {latest_ver}")
            return None, None

        # Get download URL for specific OS
        download_url_raw = download_button.get("href")
        download_url: Optional[str] = None
        if download_url_raw and isinstance(download_url_raw, str):
            if not download_url_raw.startswith("http"):
                download_url = f"https://www.python.org{download_url_raw}"
            else:
                download_url = download_url_raw

        return latest_ver, download_url

    except requests.Timeout:
        print("Error: Request to python.org timed out. Check your internet connection.")
        return None, None
    except requests.RequestException as e:
        print(f"Error: Network request failed: {e}")
        return None, None
    except Exception as e:
        print(f"Error: Unexpected error while fetching Python info: {e}")
        return None, None


def get_active_python_releases() -> list[dict]:
    """Fetch active/supported Python releases from python.org"""
    URL = "https://www.python.org/downloads/"
    releases = []

    try:
        response = requests.get(URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Parse the page text to extract release info
        # The structure is: version, status, Download, first_release, end_support, PEP
        text = soup.get_text()
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Find start of active releases (after "Release schedule" header line)
        start_idx = None
        for i, line in enumerate(lines):
            if line == "Release schedule":
                start_idx = i + 1
                break

        if start_idx:
            # Parse in groups: version, status, Download, first_release, end_support, PEP
            i = start_idx
            while i < len(lines) - 5:
                line = lines[i]
                # Check if this line is a version series (e.g., "3.14")
                if re.match(r"^\d+\.\d+$", line):
                    series = line
                    status = lines[i + 1] if i + 1 < len(lines) else ""
                    # Skip "Download" link
                    first_release = lines[i + 3] if i + 3 < len(lines) else ""
                    end_support = lines[i + 4] if i + 4 < len(lines) else ""

                    # Stop if we hit a non-release line
                    if not status or status.startswith("Looking for"):
                        break

                    releases.append(
                        {
                            "series": series,
                            "status": status,
                            "first_release": first_release,
                            "end_of_support": end_support,
                            "latest_version": None,
                        }
                    )
                    i += 6  # Move to next release block
                else:
                    i += 1

        # Get the latest patch version for each series from release links
        release_links = soup.find_all("span", class_="release-number")
        series_versions: dict = {}

        for release in release_links:
            link = release.find("a")
            if link:
                version_text = link.get_text(strip=True)
                if version_text.startswith("Python "):
                    ver = version_text.replace("Python ", "")
                    if validate_version_string(ver):
                        parts = ver.split(".")
                        if len(parts) >= 2:
                            series = f"{parts[0]}.{parts[1]}"
                            if series not in series_versions:
                                series_versions[series] = ver

        # Attach latest versions to releases
        for rel in releases:
            if rel["series"] in series_versions:
                rel["latest_version"] = series_versions[rel["series"]]

        return releases

    except Exception as e:
        print(f"Error fetching active releases: {e}")
        return []


def get_available_python_versions(limit: int = 50) -> list[dict]:
    """Fetch all available Python versions from python.org"""
    URL = "https://www.python.org/downloads/"
    versions = []

    try:
        response = requests.get(URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Find all release links
        release_links = soup.find_all("span", class_="release-number")

        for release in release_links[:limit]:
            link = release.find("a")
            if link:
                version_text = link.get_text(strip=True)
                # Extract version number (e.g., "Python 3.12.1" -> "3.12.1")
                if version_text.startswith("Python "):
                    ver = version_text.replace("Python ", "")
                    if validate_version_string(ver):
                        versions.append({"version": ver, "url": f"https://www.python.org{link.get('href', '')}"})

        return versions

    except Exception as e:
        print(f"Error fetching available versions: {e}")
        return []


def download_file(url: str, destination: str, max_retries: int = MAX_RETRIES) -> bool:
    """Download a file with retry logic, progress indication, and cleanup"""
    if not url.startswith(("http://", "https://")):
        click.echo(f"❌ Invalid URL: {url}")
        return False

    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT)

            # 4xx Client Errors: Do not retry (e.g., 404 Not Found)
            if 400 <= response.status_code < 500:
                click.echo(f"❌ Download failed with client error {response.status_code}")
                return False

            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            chunk_size = 8192

            with (
                open(destination, "wb") as f,
                click.progressbar(
                    length=total_size,
                    label="⬇ Downloading",
                    show_eta=True,
                    show_percent=True,
                ) as bar,
            ):
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))

            # Verify file
            if not os.path.exists(destination):
                click.echo("❌ Download failed: file not found")
                return False

            # Verify size
            if total_size and os.path.getsize(destination) != total_size:
                click.echo(f"❌ File size mismatch. Expected {total_size}, got {os.path.getsize(destination)}")
                raise OSError("File size mismatch")

            return True

        except (OSError, requests.RequestException) as e:
            # Cleanup partial file
            if os.path.exists(destination):
                try:
                    os.remove(destination)
                except OSError:
                    pass

            if attempt < max_retries - 1:
                wait_time = RETRY_DELAY * (attempt + 1)
                click.echo(f"\n⚠️ Attempt {attempt + 1} failed: {e}")
                click.echo(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                click.echo(f"\n❌ All download attempts failed: {e}")
                return False

    return False


def update_python_windows(version_str: str) -> bool:
    """Update Python on Windows"""
    print("\n🪟 Windows detected - Downloading Python installer...")

    # Validate version string
    if not validate_version_string(version_str):
        print(f"Error: Invalid version string: {version_str}")
        return False

    # Construct Windows installer URL - safely
    try:
        parts = version_str.split(".")
        if len(parts) < 3:
            print(f"Error: Version string must have major.minor.patch format: {version_str}")
            return False
        major, minor, _patch = parts[0], parts[1], parts[2]
    except (ValueError, IndexError) as e:
        print(f"Error parsing version string '{version_str}': {e}")
        return False

    # Detect architecture - handle ARM64, AMD64, and default to win32
    machine = platform.machine().lower()
    if machine in ["amd64", "x86_64"]:
        arch = "amd64"
    elif machine in ["arm64", "aarch64"]:
        # ARM64 Windows installers are only available for Python 3.11+
        # Fall back to AMD64 for older versions
        try:
            major_int = int(major)
            minor_int = int(minor)
            if major_int < 3 or (major_int == 3 and minor_int < 11):
                print("ARM64 installers are only available for Python 3.11+")
                print(f"Falling back to AMD64 installer for Python {version_str}")
                arch = "amd64"
            else:
                arch = "arm64"
        except (ValueError, TypeError):
            # default to AMD64 for safety
            print("Could not parse version, falling back to AMD64")
            arch = "amd64"
    else:
        arch = "win32"
    installer_url = f"https://www.python.org/ftp/python/{version_str}/python-{version_str}-{arch}.exe"

    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, f"python-{version_str}-installer.exe")

    print(f"Downloading from: {installer_url}")
    if not download_file(installer_url, installer_path):
        return False

    print("\n⚠️  Starting installer...")
    print("Please follow the installer prompts.")
    print("Recommendation: Check 'Add Python to PATH'")

    try:
        # Run installer (interactive mode) - using list instead of shell
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
        # Cleanup - with better error handling
        try:
            if os.path.exists(installer_path):
                os.remove(installer_path)
                print("Cleaned up temporary installer file")
        except PermissionError:
            print(f"Warning: Could not delete temporary file {installer_path} (permission denied)")
        except OSError as e:
            print(f"Warning: Could not delete temporary file {installer_path}: {e}")


def update_python_linux(version_str: str) -> bool:
    """Install Python on Linux using mise, pyenv, or package manager"""
    print("\n[Linux] Installing Python...")

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

    # Priority 1: Use mise if available (modern, no sudo needed)
    if shutil.which("mise"):
        print("Using mise to install Python...")
        print(f"Installing Python {version_str}...")

        try:
            # Install the Python version
            result = subprocess.run(["mise", "install", f"python@{version_str}"], check=False, capture_output=False)

            if result.returncode != 0:
                print(f"Warning: mise install returned code {result.returncode}")
                # Try with just major.minor
                print(f"Trying with python@{major_minor}...")
                result = subprocess.run(["mise", "install", f"python@{major_minor}"], check=False, capture_output=False)

            if result.returncode == 0:
                print(f"\n[OK] Python {version_str} installed via mise!")
                print("\nTo use this version:")
                print(f"  mise use python@{version_str}     # Use in current directory")
                print(f"  mise use -g python@{version_str}  # Set as global default")
                return True
            else:
                print("mise installation failed, trying other methods...")
        except Exception as e:
            print(f"mise error: {e}")

    # Priority 2: Use pyenv if available
    if shutil.which("pyenv"):
        print("Using pyenv to install Python...")

        try:
            result = subprocess.run(["pyenv", "install", version_str], check=False, capture_output=False)

            if result.returncode == 0:
                print(f"\n[OK] Python {version_str} installed via pyenv!")
                print("\nTo use this version:")
                print(f"  pyenv local {version_str}   # Use in current directory")
                print(f"  pyenv global {version_str}  # Set as global default")
                return True
            else:
                print("pyenv installation failed, trying other methods...")
        except Exception as e:
            print(f"pyenv error: {e}")

    # Priority 3: Use apt (deadsnakes PPA)
    if shutil.which("apt"):
        print("Using apt package manager...")
        print("\nThis requires sudo privileges and adds the deadsnakes PPA.")
        print("Your existing Python will remain unchanged.")

        commands = [
            ["sudo", "apt", "update"],
            ["sudo", "apt", "install", "-y", "software-properties-common"],
            ["sudo", "add-apt-repository", "-y", "ppa:deadsnakes/ppa"],
            ["sudo", "apt", "update"],
            ["sudo", "apt", "install", "-y", f"python{major_minor}"],
            ["sudo", "apt", "install", "-y", f"python{major_minor}-venv", f"python{major_minor}-distutils"],
        ]

        for cmd in commands:
            print(f"Running: {' '.join(cmd)}")
            try:
                result = subprocess.run(cmd, check=False, capture_output=False)
                if result.returncode != 0:
                    print(f"Warning: Command returned {result.returncode}")
            except Exception as e:
                print(f"Error: {e}")
                return False

        python_path = f"/usr/bin/python{major_minor}"
        if os.path.exists(python_path):
            print(f"\n[OK] Python {major_minor} installed at {python_path}")
            return True
        else:
            print(f"Warning: {python_path} not found")
            return False

    elif shutil.which("dnf") or shutil.which("yum"):
        pkg_mgr = "dnf" if shutil.which("dnf") else "yum"
        print(f"Using {pkg_mgr}...")
        print(f"\nRun manually: sudo {pkg_mgr} install python3")
        print("Consider installing mise or pyenv for version control.")
        return False

    else:
        print("No package manager found.")
        print("\nRecommended: Install mise for easy version management")
        print("  curl https://mise.run | sh")
        print(f"  mise install python@{version_str}")
        return False


def update_python_macos(version_str: str) -> bool:
    """Update Python on macOS using mise, pyenv, Homebrew, or official installer"""
    print("\n[macOS] Installing Python...")

    # Validate version string
    if not validate_version_string(version_str):
        print(f"Error: Invalid version string: {version_str}")
        return False

    # Extract version numbers for logic
    try:
        parts = version_str.split(".")
        if len(parts) < 2:
            print(f"Error: Invalid version format: {version_str}")
            return False

        # Convert to integers for comparison (Requested by maintainer)
        major = int(parts[0])
        minor = int(parts[1])
        major_minor = f"{major}.{minor}"

    except (ValueError, IndexError) as e:
        print(f"Error parsing version: {e}")
        return False

    # Priority 1: Use mise if available
    if shutil.which("mise"):
        print("Using mise to install Python...")
        print(f"Installing Python {version_str}...")

        try:
            result = subprocess.run(["mise", "install", f"python@{version_str}"], check=False, capture_output=False)

            if result.returncode != 0:
                print(f"Trying with python@{major_minor}...")
                result = subprocess.run(["mise", "install", f"python@{major_minor}"], check=False, capture_output=False)

            if result.returncode == 0:
                print(f"\n[OK] Python {version_str} installed via mise!")
                print("\nTo use this version:")
                print(f"  mise use python@{version_str}     # Use in current directory")
                print(f"  mise use -g python@{version_str}  # Set as global default")
                return True
            else:
                print("mise installation failed, trying other methods...")
        except Exception as e:
            print(f"mise error: {e}")

    # Priority 2: Use pyenv if available
    if shutil.which("pyenv"):
        print("Using pyenv to install Python...")

        try:
            result = subprocess.run(["pyenv", "install", version_str], check=False, capture_output=False)

            if result.returncode == 0:
                print(f"\n[OK] Python {version_str} installed via pyenv!")
                print("\nTo use this version:")
                print(f"  pyenv local {version_str}   # Use in current directory")
                print(f"  pyenv global {version_str}  # Set as global default")
                return True
            else:
                print("pyenv installation failed, trying other methods...")
        except Exception as e:
            print(f"pyenv error: {e}")

    # Priority 3: Use Homebrew
    if shutil.which("brew"):
        print("Using Homebrew...")
        try:
            print("Updating Homebrew...")
            subprocess.run(["brew", "update"], check=False, capture_output=True)

            formula_name = f"python@{major_minor}"
            print(f"Installing Python {version_str} via Homebrew (formula: {formula_name})...")
            result = subprocess.run(["brew", "install", formula_name], check=False)

            if result.returncode == 0:
                print(f"[OK] Python {version_str} installed via Homebrew")
                return True
            else:
                print("Homebrew install failed. Falling back to direct installer...")
        except Exception as e:
            print(f"Error running Homebrew: {e}")
            # Do not return False here; let it fall through to the direct installer

    # FALLBACK: Direct Download (Official Installer)
    # This runs if no package managers are found OR if they failed above.
    print("\nNo package manager found or installation failed.")
    print("Falling back to official Python.org installer...")

    # Determine correct installer suffix based on Python version
    # Python 3.9+ uses 'macos11.pkg' (Universal2)
    # Python 3.8 and older use 'macosx10.9.pkg'
    if major > 3 or (major == 3 and minor >= 9):
        installer_suffix = "macos11.pkg"
    else:
        installer_suffix = "macosx10.9.pkg"

    installer_filename = f"python-{version_str}-{installer_suffix}"
    macos_installer_url = f"https://www.python.org/ftp/python/{version_str}/{installer_filename}"

    # Prepare paths
    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, installer_filename)

    print(f"Downloading from: {macos_installer_url}")

    # Download (using the existing helper function in your file)
    if not download_file(macos_installer_url, installer_path):
        return False

    # Install
    print("\n⚠️  Starting installer...")
    print("You may be prompted for your sudo password to allow installation.")
    try:
        # Run the macOS installer command
        subprocess.run(["sudo", "installer", "-pkg", installer_path, "-target", "/"], check=True)
        print(f"\n[OK] Python {version_str} successfully installed!")
        return True

    except subprocess.CalledProcessError:
        print("Error: Installer failed.")
        return False
    except PermissionError:
        print("Error: Permission denied. Please run with sudo.")
        return False
    finally:
        # Cleanup
        if os.path.exists(installer_path):
            try:
                os.remove(installer_path)
            except OSError:
                pass


def is_python_version_installed(version_str: str) -> bool:
    """Check if a specific Python version is installed on the system"""
    installed = get_installed_python_versions()
    
    # 1. Try exact match
    if any(v["version"] == version_str for v in installed):
        return True
        
    # 2. Try major.minor match (especially for Windows where 'py --list' returns only major.minor)
    try:
        parts = version_str.split(".")
        if len(parts) >= 2:
            major_minor = f"{parts[0]}.{parts[1]}"
            return any(v["version"] == major_minor for v in installed)
    except (ValueError, IndexError):
        pass
        
    return False


def remove_python_windows(version_str: str) -> bool:
    """
    Remove Python on Windows.
    Assumes it was installed using the official Python.org installer.
    """
    print(f"\n[Windows] Attempting to remove Python {version_str}...")

    # Validation step
    if not is_python_version_installed(version_str):
        print(f"Error: Python {version_str} is not installed.")
        return False

    # Check if it's the running version (major.minor comparison)
    current_ver = platform.python_version()
    current_parts = current_ver.split(".")
    target_parts = version_str.split(".")

    if len(current_parts) >= 2 and len(target_parts) >= 2:
        if current_parts[0] == target_parts[0] and current_parts[1] == target_parts[1]:
            print(f"Error: Cannot remove Python {version_str} as it matches the currently running major.minor version ({current_ver}).")
            return False

    # Try to find the installer in temp directory
    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, f"python-{version_str}-installer.exe")

    # Fallback message for Windows
    fallback_msg = (
        "\n[Notice] Automated uninstallation on Windows encountered issues.\n"
        "If you installed Python via the Microsoft Store, please remove it manually via:\n"
        "Windows Settings -> Apps -> Installed apps -> Python -> Uninstall."
    )

    # Priority 1: Try winget (handles MS Store and many installers)
    if shutil.which("winget"):
        print(f"Attempting to uninstall via winget...")
        # MS Store IDs usually follow: PythonSoftwareFoundation.Python.3.X
        # We try both the generic name and potential MS Store ID
        major_minor = ".".join(version_str.split(".")[:2])
        potential_ids = [
            f"Python.Python.{major_minor}",
            f"PythonSoftwareFoundation.Python.{major_minor}"
        ]
        
        for pkg_id in potential_ids:
            try:
                # --silent --accept-source-agreements --accept-package-agreements
                result = subprocess.run(
                    ["winget", "uninstall", "--id", pkg_id, "--silent"],
                    capture_output=True, text=True, check=False
                )
                if result.returncode == 0:
                    print(f"[OK] Python {version_str} removed via winget ({pkg_id})")
                    return True
            except Exception:
                continue

    # Priority 2: Try PowerShell for Microsoft Store (if winget failed or not present)
    major_minor = ".".join(version_str.split(".")[:2])
    print(f"Checking for Microsoft Store installation (Python {major_minor})...")
    ps_check = (
        f'Get-AppxPackage | Where-Object {{$_.Name -like "*Python.{major_minor}*"}} | '
        'Select-Object -ExpandProperty PackageFullName'
    )
    try:
        check_result = subprocess.run(
            ["powershell", "-Command", ps_check],
            capture_output=True, text=True, check=False
        )
        package_fullname = check_result.stdout.strip()
        
        if package_fullname:
            print(f"Found Microsoft Store package: {package_fullname}")
            print("Attempting to remove via PowerShell...")
            remove_command = f'Remove-AppxPackage -Package "{package_fullname}"'
            remove_result = subprocess.run(
                ["powershell", "-Command", remove_command],
                capture_output=True, text=True, check=False
            )
            
            if remove_result.returncode == 0:
                print(f"[OK] Python {version_str} (MS Store) removed successfully!")
                return True
            else:
                print(f"PowerShell removal failed: {remove_result.stderr.strip()}")
    except Exception as e:
        print(f"Error checking Microsoft Store packages: {e}")

    # Priority 3: Use official installer if available
    if not os.path.exists(installer_path):
        print("\nInstaller not found in temporary directory.")
        print("Attempting to download the matching installer for removal...")
        
        # Detect architecture
        machine = platform.machine().lower()
        if machine in ["amd64", "x86_64"]:
            arch = "amd64"
        elif machine in ["arm64", "aarch64"]:
            arch = "arm64"
        else:
            arch = "win32"
            
        installer_url = f"https://www.python.org/ftp/python/{version_str}/python-{version_str}-{arch}.exe"
        print(f"Downloading from: {installer_url}")
        
        if not download_file(installer_url, installer_path):
            print("Failed to download installer.")
            print(fallback_msg)
            return False

    print(f"Running uninstaller: {installer_path} /uninstall")
    try:
        # Run uninstaller (interactive)
        result = subprocess.run([installer_path, "/uninstall"], check=False)
        
        # Cleanup downloaded installer after use
        try:
            if os.path.exists(installer_path):
                os.remove(installer_path)
        except OSError:
            pass
            
        if result.returncode == 0:
            print(f"\n[OK] Python {version_str} removed successfully!")
            return True
        else:
            print(f"Warning: Uninstaller exited with code {result.returncode}")
            print(fallback_msg)
            return False
    except Exception as e:
        print(f"Error during uninstallation: {e}")
        print(fallback_msg)
        return False


def remove_python_linux(version_str: str) -> bool:
    """
    Remove Python on Linux.
    Supports apt removal with safety checks.
    """
    print(f"\n[Linux] Attempting to remove Python {version_str}...")

    # Validation step
    if not is_python_version_installed(version_str):
        print(f"Error: Python {version_str} is not installed.")
        return False

    # Major/minor comparison for safety
    try:
        parts = version_str.split(".")
        major_minor = f"{parts[0]}.{parts[1]}"
        current_parts = platform.python_version().split(".")
        current_major_minor = f"{current_parts[0]}.{current_parts[1]}"

        if major_minor == current_major_minor:
            print(f"Error: Cannot remove Python {version_str} as it matches the currently running major.minor version.")
            return False
    except (ValueError, IndexError):
        pass

    # Safety check: Don't remove if it's the system Python
    system_python_path = "/usr/bin/python3"
    if os.path.exists(system_python_path):
        try:
            result = subprocess.run([system_python_path, "--version"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                system_ver = result.stdout.strip().replace("Python ", "")
                system_parts = system_ver.split(".")
                if len(system_parts) >= 2:
                    system_major_minor = f"{system_parts[0]}.{system_parts[1]}"
                    if major_minor == system_major_minor:
                        print(f"CRITICAL WARNING: Python {major_minor} appears to be the system Python.")
                        print("Removing it may break your operating system (package managers, GUI, etc.).")
                        print("Aborting for safety.")
                        return False
        except Exception:
            pass

    # Try mise
    if shutil.which("mise"):
        try:
            result = subprocess.run(["mise", "uninstall", f"python@{version_str}"], check=False)
            if result.returncode == 0:
                print(f"[OK] Python {version_str} uninstalled via mise.")
                return True
        except Exception:
            pass

    # Try pyenv
    if shutil.which("pyenv"):
        try:
            result = subprocess.run(["pyenv", "uninstall", "-f", version_str], check=False)
            if result.returncode == 0:
                print(f"[OK] Python {version_str} uninstalled via pyenv.")
                return True
        except Exception:
            pass

    # Use apt (with safety checks and warnings)
    if shutil.which("apt"):
        pkg_name = f"python{major_minor}"
        try:
            # Check if installed via apt
            check_pkg = subprocess.run(["dpkg", "-l", pkg_name], capture_output=True, text=True, check=False)
            if check_pkg.returncode == 0:
                print(f"\n⚠️  WARNING: You are about to remove '{pkg_name}' using apt.")
                print("   This is a system-wide package and removal requires sudo.")
                print("   Ensure this is not a critical system package.")

                if not click.confirm("Do you want to proceed?"):
                    print("Removal cancelled.")
                    return False

                print(f"Removing {pkg_name}...")
                subprocess.run(["sudo", "apt", "remove", "-y", pkg_name], check=False)
                subprocess.run(["sudo", "apt", "autoremove", "-y"], check=False)
                return True
        except Exception as e:
            print(f"Error during apt removal: {e}")

    print("\nCould not find a safe automated way to remove this Python installation.")
    print("Please remove it manually using your package manager.")
    return False


def remove_python_macos(version_str: str) -> bool:
    """
    Remove Python on macOS.
    Defers risky cases to manual removal.
    """
    print(f"\n[macOS] Attempting to remove Python {version_str}...")

    # Validation step
    if not is_python_version_installed(version_str):
        print(f"Error: Python {version_str} is not installed.")
        return False

    # Check major.minor
    try:
        parts = version_str.split(".")
        major_minor = f"{parts[0]}.{parts[1]}"
        current_parts = platform.python_version().split(".")
        current_major_minor = f"{current_parts[0]}.{current_parts[1]}"

        if major_minor == current_major_minor:
            print(f"Error: Cannot remove Python {version_str} as it matches the currently running major.minor version.")
            return False
    except (ValueError, IndexError):
        pass

    # Try mise
    if shutil.which("mise"):
        try:
            result = subprocess.run(["mise", "uninstall", f"python@{version_str}"], check=False)
            if result.returncode == 0:
                print(f"[OK] Python {version_str} uninstalled via mise.")
                return True
        except Exception:
            pass

    # Try pyenv
    if shutil.which("pyenv"):
        try:
            result = subprocess.run(["pyenv", "uninstall", "-f", version_str], check=False)
            if result.returncode == 0:
                print(f"[OK] Python {version_str} uninstalled via pyenv.")
                return True
        except Exception:
            pass

    # Try Homebrew
    if shutil.which("brew"):
        try:
            pkg_name = f"python@{major_minor}"
            check_brew = subprocess.run(["brew", "list", pkg_name], capture_output=True, text=True, check=False)
            if check_brew.returncode == 0:
                print(f"Uninstalling {pkg_name} via Homebrew...")
                subprocess.run(["brew", "uninstall", pkg_name], check=False)
                return True
        except Exception:
            pass

    print("\n[Notice] Automated removal of official Python.org installations on macOS is complex.")
    print("To safely remove it, please delete the following manually:")
    print(f"1. /Applications/Python {major_minor}")
    print(f"2. /Library/Frameworks/Python.framework/Versions/{major_minor}")
    return False


def check_python_version(silent: bool = False) -> Tuple[str, Optional[str], bool]:
    """
    Check local Python version against the latest stable version from python.org
    Returns: (local_version, latest_version, needs_update)
    """
    local_ver = platform.python_version()

    if not silent:
        print(f"Checking Python version... (Current: {local_ver})")

    # Use retry logic
    latest_ver, _ = get_latest_python_info_with_retry()

    if not latest_ver:
        if not silent:
            print("Error: Could not fetch latest version information.")
            print("Please check your internet connection and try again.")
        return local_ver, None, False

    try:
        # Validate latest version
        if not validate_version_string(latest_ver):
            if not silent:
                print(f"Error: Invalid version format from server: {latest_ver}")
            return local_ver, None, False

        # Use 'version.parse' to create comparable version objects
        local_version_obj = pkg_version.parse(local_ver)
        latest_version_obj = pkg_version.parse(latest_ver)
        needs_update = local_version_obj < latest_version_obj

        if not silent:
            # Display Results
            print("\n" + "=" * 40)
            print("     Python Version Check Report")
            print("=" * 40)
            print(f"Your version:   {local_ver}")
            print(f"Latest version: {latest_ver}")
            print("=" * 40)

            if not needs_update:
                print("✓ You are up-to-date!")
            else:
                print(f"⚠ A new version ({latest_ver}) is available!")

        return local_ver, latest_ver, needs_update

    except Exception as e:
        if not silent:
            print(f"Error comparing versions: {e}")
            print("This might be due to an unexpected version format.")
        return local_ver, latest_ver, False


def show_python_usage_instructions(version_str: str, os_name: str) -> None:
    """
    Show user how to use the newly installed Python version.
    Does NOT modify system defaults - just provides instructions.
    """
    # Extract major.minor for display
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

    if os_name == "linux" or os_name == "darwin":
        click.echo("\n1️⃣  Run scripts with the new version:")
        click.echo(f"    python{major_minor} your_script.py")

        click.echo("\n2️⃣  Create a virtual environment:")
        click.echo(f"    python{major_minor} -m venv myproject")
        click.echo("    source myproject/bin/activate")
        click.echo(f"    python --version  # Will show {version_str}")

        click.echo("\n3️⃣  Check it's installed:")
        click.echo(f"    python{major_minor} --version")

    elif os_name == "windows":
        click.echo("\n1️⃣  Use Python Launcher:")
        click.echo(f"    py -{major_minor} your_script.py")

        click.echo("\n2️⃣  List all Python versions:")
        click.echo("    py --list")

        click.echo("\n3️⃣  Create a virtual environment:")
        click.echo(f"    py -{major_minor} -m venv myproject")
        click.echo("    myproject\\Scripts\\activate")

    click.echo("-" * 60)
    click.echo("\n💡 Important: Your old Python version remains as system default.")
    click.echo("    This prevents breaking system tools and existing scripts.")
    click.echo("    Use the specific version command when you need the new Python.")
    click.echo("\n⚠️  Note: Restart your terminal to ensure PATH is updated.")


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--version", "-v", is_flag=True, help="Show tool version")
def cli(ctx, version):
    """Python Version Manager - Check and install Python (does NOT modify system defaults)"""
    if version:
        click.echo("Python Version Manager v2.0.1")
        ctx.exit()

    if ctx.invoked_subcommand is None:
        # Default behavior: just check version
        ctx.invoke(check)


@cli.command()
def check():
    """Check current Python version against latest stable release"""
    try:
        local_ver, latest_ver, needs_update = check_python_version(silent=False)

        if needs_update:
            click.echo("\n💡 Tip: Run 'pyvm update' to upgrade Python")
            sys.exit(1)  # Exit code 1 indicates update available
        else:
            sys.exit(0)  # Exit code 0 indicates up-to-date

    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled by user.")
        sys.exit(130)


@cli.command()
@click.argument("version")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def install(version, yes):
    """Install a specific Python version

    Examples:
        pyvm install 3.12.1
        pyvm install 3.11.5 --yes
    """
    try:
        # Validate version format
        if not validate_version_string(version) or len(version.split(".")) < 3:
            click.echo(f"Error: Invalid version format: {version}")
            click.echo("Version must be in format: X.Y.Z (e.g., 3.12.1)")
            sys.exit(1)

        local_ver = platform.python_version()
        click.echo(f"Current Python: {local_ver}")
        click.echo(f"Target version: {version}")

        # Check if same version
        if local_ver == version:
            click.echo(f"\nPython {version} is already your current version.")
            sys.exit(0)

        os_name, arch = get_os_info()
        click.echo(f"System: {os_name.title()} ({arch})")

        # Confirm installation
        if not yes:
            if not click.confirm(f"\nInstall Python {version}?"):
                click.echo("Installation cancelled.")
                sys.exit(0)

        click.echo(f"\nInstalling Python {version}...")

        # Perform installation based on OS
        success = False
        if os_name == "windows":
            success = update_python_windows(version)
        elif os_name == "linux":
            success = update_python_linux(version)
        elif os_name == "darwin":
            success = update_python_macos(version)
        else:
            click.echo(f"Unsupported operating system: {os_name}")
            sys.exit(1)

        if success:
            show_python_usage_instructions(version, os_name)
        else:
            click.echo("\nInstallation encountered issues. Check messages above.")
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled.")
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nError: {e}")
        sys.exit(1)


@cli.command()
@click.argument("version")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def remove(version, yes):
    """Remove a specific Python version"""
    try:
        # Validate version format
        if not validate_version_string(version):
            click.echo(f"Error: Invalid version format: {version}")
            sys.exit(1)

        os_name, _ = get_os_info()

        # Confirm removal
        if not yes:
            if not click.confirm(f"\nAre you sure you want to remove Python {version}?"):
                click.echo("Removal cancelled.")
                sys.exit(0)

        success = False
        if os_name == "windows":
            success = remove_python_windows(version)
        elif os_name == "linux":
            success = remove_python_linux(version)
        elif os_name == "darwin":
            success = remove_python_macos(version)
        else:
            click.echo(f"Unsupported operating system: {os_name}")
            sys.exit(1)

        if success:
            click.echo(f"\nSuccessfully removed Python {version}")
        else:
            click.echo("\nRemoval encountered issues. Check messages above.")
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled.")
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nError: {e}")
        sys.exit(1)


@cli.command("list")
@click.option("--all", "-a", "show_all", is_flag=True, help="Show all versions including patch releases")
def list_versions(show_all):
    """List available Python versions

    By default shows active release series with their support status.
    Use --all to see all individual patch versions.
    """
    try:
        click.echo("Fetching Python versions...\n")

        local_ver = platform.python_version()
        local_series = ".".join(local_ver.split(".")[:2])

        if show_all:
            # Show all individual versions
            versions = get_available_python_versions(limit=100)

            if not versions:
                click.echo("Could not fetch available versions.")
                sys.exit(1)

            latest_ver, _ = get_latest_python_info_with_retry()

            click.echo(f"{'VERSION':<12} {'STATUS'}")
            click.echo("-" * 40)

            for v in versions:
                ver = v["version"]
                status = ""
                if ver == local_ver:
                    status = "(installed)"
                elif latest_ver and ver == latest_ver:
                    status = "(latest)"

                click.echo(f"{ver:<12} {status}")
        else:
            # Show active release series
            releases = get_active_python_releases()

            if not releases:
                click.echo("Could not fetch active releases.")
                sys.exit(1)

            click.echo(f"{'SERIES':<10} {'LATEST':<12} {'STATUS':<15} {'SUPPORT UNTIL'}")
            click.echo("-" * 55)

            for rel in releases:
                series = rel["series"]
                latest = rel.get("latest_version") or "-"
                status = rel.get("status", "")
                end_support = rel.get("end_of_support", "")

                # Mark if this is the user's installed series
                marker = ""
                if series == local_series:
                    marker = " *"

                # Color code status
                if "pre-release" in status.lower():
                    status_display = "pre-release"
                elif "bugfix" in status.lower():
                    status_display = "bugfix"
                elif "security" in status.lower():
                    status_display = "security"
                elif "end of life" in status.lower():
                    status_display = "end-of-life"
                else:
                    status_display = status

                click.echo(f"{series:<10} {latest:<12} {status_display:<15} {end_support}{marker}")

            click.echo(f"\n * = your installed version ({local_ver})")
            click.echo("\nUse 'pyvm list --all' to see all patch versions")

        click.echo("Install with: pyvm install <version>")

    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled.")
        sys.exit(130)
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.option("--auto", is_flag=True, help="Automatically proceed without confirmation")
@click.option("--version", "target_version", default=None, help="Specify a target Python version (e.g., 3.11.5)")
def update(auto, target_version):
    """Download and install Python version (does NOT modify system defaults)

    By default, installs the latest version. Use --version to specify a particular version.
    """
    try:
        local_ver = platform.python_version()
        install_version = None

        if target_version:
            # Validate specified version
            if not validate_version_string(target_version) or len(target_version.split(".")) < 3:
                click.echo(f"❌ Error: Invalid version format: {target_version}")
                click.echo("Version must be in format: X.Y.Z (e.g., 3.11.5)")
                sys.exit(1)

            install_version = target_version
            click.echo(f"📌 Target version specified: {install_version}")
            click.echo(f"📊 Current version: {local_ver}")
        else:
            # Check for latest version
            click.echo("🔍 Checking for updates...")
            local_ver, latest_ver, needs_update = check_python_version(silent=True)

            if not latest_ver:
                click.echo("❌ Could not fetch latest version information.")
                sys.exit(1)

            click.echo(f"\n📊 Current version: {local_ver}")
            click.echo(f"📊 Latest version:  {latest_ver}")

            if not needs_update:
                click.echo("\n✅ You already have the latest version!")
                sys.exit(0)

            click.echo(f"\n🚀 Update available: {local_ver} → {latest_ver}")
            install_version = latest_ver

        # Confirm update
        if not auto:
            if not click.confirm(f"\nDo you want to proceed with installing Python {install_version}?"):
                click.echo("Installation cancelled.")
                sys.exit(0)

        # Check admin privileges for some operations
        os_name, arch = get_os_info()
        click.echo(f"\n🖥️  Detected: {os_name.title()} ({arch})")

        # Perform update based on OS
        success = False
        if os_name == "windows":
            success = update_python_windows(install_version)
        elif os_name == "linux":
            success = update_python_linux(install_version)
        elif os_name == "darwin":
            success = update_python_macos(install_version)
        else:
            click.echo(f"❌ Unsupported operating system: {os_name}")
            sys.exit(1)

        if success:
            # Show usage instructions (safe, no system modifications)
            show_python_usage_instructions(install_version, os_name)
        else:
            click.echo("\n⚠️  Installation process encountered issues.")
            click.echo("    Please check the messages above.")
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")
        sys.exit(1)


@cli.command()
def tui():
    """Launch the interactive TUI interface"""
    try:
        from pyvm_tui import run_tui

        run_tui()
    except ImportError:
        click.echo("❌ TUI mode requires the 'textual' package.")
        click.echo("Install it with: pip install pyvm-updater[tui]")
        click.echo("Or: pip install textual")
        sys.exit(1)


@cli.command()
def info():
    """Show detailed system and Python information"""
    try:
        click.echo("=" * 50)
        click.echo("           System Information")
        click.echo("=" * 50)

        os_name, arch = get_os_info()
        click.echo(f"Operating System: {os_name.title()}")
        click.echo(f"Architecture:     {arch}")
        click.echo(f"Python Version:   {platform.python_version()}")
        click.echo(f"Python Path:      {sys.executable}")
        click.echo(f"Platform:         {platform.platform()}")

        click.echo(f"\nAdmin/Sudo:       {'Yes' if is_admin() else 'No'}")

        # Show python3 command location if different
        try:
            result = subprocess.run(["which", "python3"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                python3_path = result.stdout.strip()
                if python3_path != sys.executable:
                    click.echo(f"python3 command:  {python3_path}")
        except Exception:
            pass

        click.echo("=" * 50)

    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


def main():
    """Main entry point for the script"""
    try:
        cli()
    except Exception as e:
        click.echo(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
