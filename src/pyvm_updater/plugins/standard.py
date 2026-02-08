"""Standard installer plugins for pyvm_updater."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ..utils import download_file, validate_version_string, verify_file_checksum
from ..version import is_python_version_installed
from .base import InstallerPlugin


class MiseInstaller(InstallerPlugin):
    """Installer using mise-en-place."""

    def get_name(self) -> str:
        return "mise"

    def is_supported(self) -> bool:
        return bool(shutil.which("mise"))

    def install(self, version: str, **kwargs: Any) -> bool:
        print(f"Using mise to install Python {version}...")
        try:
            result = subprocess.run(["mise", "install", f"python@{version}"], check=False)
            if result.returncode != 0:
                # Try major.minor if exact version fails
                parts = version.split(".")
                if len(parts) >= 2:
                    major_minor = f"{parts[0]}.{parts[1]}"
                    result = subprocess.run(["mise", "install", f"python@{major_minor}"], check=False)

            if result.returncode == 0:
                print(f"\n[OK] Python {version} installed via mise!")
                print(f"\nTo use: mise use python@{version}")
                return True
        except Exception as e:
            print(f"mise error: {e}")
        return False

    def uninstall(self, version: str) -> bool:
        try:
            result = subprocess.run(
                ["mise", "uninstall", f"python@{version}"],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_priority(self) -> int:
        return 100


class PyenvInstaller(InstallerPlugin):
    """Installer using pyenv."""

    def get_name(self) -> str:
        return "pyenv"

    def is_supported(self) -> bool:
        return bool(shutil.which("pyenv"))

    def install(self, version: str, **kwargs: Any) -> bool:
        print(f"Using pyenv to install Python {version}...")
        try:
            result = subprocess.run(["pyenv", "install", "-s", version], check=False)
            if result.returncode == 0:
                print(f"\n[OK] Python {version} installed via pyenv!")
                return True
        except Exception as e:
            print(f"pyenv error: {e}")
        return False

    def uninstall(self, version: str) -> bool:
        try:
            result = subprocess.run(
                ["pyenv", "uninstall", "-f", version],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_priority(self) -> int:
        return 90


class BrewInstaller(InstallerPlugin):
    """Installer using Homebrew (macOS)."""

    def get_name(self) -> str:
        return "brew"

    def is_supported(self) -> bool:
        return platform.system() == "Darwin" and bool(shutil.which("brew"))

    def install(self, version: str, **kwargs: Any) -> bool:
        parts = version.split(".")
        if len(parts) < 2:
            return False
        major_minor = f"{parts[0]}.{parts[1]}"

        print(f"Using Homebrew to install Python {major_minor}...")
        try:
            subprocess.run(["brew", "update"], check=False, capture_output=True)
            result = subprocess.run(["brew", "install", f"python@{major_minor}"], check=False)
            if result.returncode == 0:
                print(f"[OK] Python {version} installed via Homebrew")
                return True
        except Exception as e:
            print(f"Homebrew error: {e}")
        return False

    def uninstall(self, version: str) -> bool:
        parts = version.split(".")
        if len(parts) < 2:
            return False
        major_minor = f"{parts[0]}.{parts[1]}"
        pkg_name = f"python@{major_minor}"

        try:
            check_brew = subprocess.run(
                ["brew", "list", pkg_name],
                capture_output=True,
                text=True,
                check=False,
            )
            if check_brew.returncode == 0:
                subprocess.run(["brew", "uninstall", pkg_name], check=False)
                return True
        except Exception:
            pass
        return False

    def get_priority(self) -> int:
        return 80


class AptInstaller(InstallerPlugin):
    """Installer using apt (Linux/Debian/Ubuntu)."""

    def get_name(self) -> str:
        return "apt"

    def is_supported(self) -> bool:
        return platform.system() == "Linux" and bool(shutil.which("apt"))

    def install(self, version: str, **kwargs: Any) -> bool:
        parts = version.split(".")
        if len(parts) < 2:
            return False
        major_minor = f"{parts[0]}.{parts[1]}"

        print("Using apt package manager...")
        sudo_prefix = ["sudo"] if shutil.which("sudo") else []
        commands = [
            sudo_prefix + ["apt", "update"],
            sudo_prefix + ["apt", "install", "-y", "software-properties-common"],
            sudo_prefix + ["add-apt-repository", "-y", "ppa:deadsnakes/ppa"],
            sudo_prefix + ["apt", "update"],
            sudo_prefix + ["apt", "install", "-y", f"python{major_minor}"],
            sudo_prefix + ["apt", "install", "-y", f"python{major_minor}-venv", f"python{major_minor}-distutils"],
        ]

        for cmd in commands:
            print(f"Running: {' '.join(cmd)}")
            try:
                result = subprocess.run(cmd, check=False)
                if result.returncode != 0:
                    print(f"Warning: Command returned {result.returncode}")
            except Exception as e:
                print(f"Error: {e}")
                return False

        python_path = f"/usr/bin/python{major_minor}"
        if os.path.exists(python_path):
            print(f"\n[OK] Python {major_minor} installed at {python_path}")
            return True
        return False

    def uninstall(self, version: str) -> bool:
        # Apt uninstallation is risky, we don't automate it here as per original code
        return False

    def get_priority(self) -> int:
        return 70


class WindowsInstaller(InstallerPlugin):
    """Official Python installer for Windows."""

    def get_name(self) -> str:
        return "windows"

    def is_supported(self) -> bool:
        return platform.system() == "Windows"

    def install(self, version: str, **kwargs: Any) -> bool:
        print(f"\n🪟 Windows detected - Downloading Python installer for {version}...")

        if not validate_version_string(version):
            print(f"Error: Invalid version string: {version}")
            return False

        try:
            parts = version.split(".")
            if len(parts) < 3:
                print(f"Error: Version must be major.minor.patch format: {version}")
                return False
            major, minor = parts[0], parts[1]
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

        installer_url = f"https://www.python.org/ftp/python/{version}/python-{version}-{arch}.exe"
        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, f"python-{version}-installer.exe")

        print(f"Downloading from: {installer_url}")
        if not download_file(installer_url, installer_path):
            return False

        checksum_url = installer_url + ".sha256"
        if not verify_file_checksum(installer_path, checksum_url):
            print("❌ Aborting installation due to integrity check failure")
            try:
                os.remove(installer_path)
            except OSError:
                pass
            return False

        print("\n⚠️  Starting installer...")
        print("Please follow the installer prompts.")

        try:
            cmd = [installer_path]

            # Add options from wizard if provided
            if kwargs.get("add_to_path"):
                cmd.append("PrependPath=1")

            if kwargs.get("install_path"):
                cmd.append(f"TargetDir={kwargs['install_path']}")

            # Default to passive installation if options are provided to avoid too much manual interaction
            if kwargs.get("add_to_path") or kwargs.get("install_path"):
                cmd.append("/passive")

            result = subprocess.run(cmd, check=False)
            if result.returncode != 0:
                # 1602: User cancelled, 1603: Fatal error during installation (common for cancellation)
                if result.returncode in [1602, 1603]:
                    print("\n❌ Installation cancelled or interrupted by user.")
                else:
                    print(f"\n❌ Installer failed with exit code {result.returncode}")
                return False

            # Additional check: If it returned 0 but was cancelled, we can't easily tell,
            # but usually returncode is reliable.
            return True
        except Exception as e:
            print(f"\n❌ Error running installer: {e}")
            return False
        finally:
            try:
                if os.path.exists(installer_path):
                    os.remove(installer_path)
            except OSError:
                pass

    def uninstall(self, version: str) -> bool:
        if not is_python_version_installed(version):
            return False

        # Try winget
        if shutil.which("winget"):
            major_minor = ".".join(version.split(".")[:2])
            potential_ids = [
                f"Python.Python.{major_minor}",
                f"PythonSoftwareFoundation.Python.{major_minor}",
            ]

            for pkg_id in potential_ids:
                try:
                    result = subprocess.run(
                        ["winget", "uninstall", "--id", pkg_id, "--silent"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if result.returncode == 0:
                        return True
                except Exception:
                    continue
        return False

    def get_priority(self) -> int:
        return 60


class MicrosoftStoreInstaller(InstallerPlugin):
    """Installer for Python from the Microsoft Store using winget."""

    def get_name(self) -> str:
        return "store"

    def is_supported(self) -> bool:
        return platform.system() == "Windows" and bool(shutil.which("winget"))

    def install(self, version: str, **kwargs: Any) -> bool:
        parts = version.split(".")
        if len(parts) < 2:
            print("Error: Version must be at least major.minor for Store installation.")
            return False
        major_minor = f"{parts[0]}.{parts[1]}"

        print(f"Using winget to install Python {major_minor} from Microsoft Store...")
        try:
            # Microsoft Store Python packages usually follow this ID pattern
            pkg_id = f"Python.Python.{major_minor}"
            result = subprocess.run(
                [
                    "winget",
                    "install",
                    "--id",
                    pkg_id,
                    "--source",
                    "msstore",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ],
                check=False,
            )

            if result.returncode == 0:
                print(f"\n[OK] Python {major_minor} installed via Microsoft Store!")
                return True
            else:
                # Try alternate ID if first one fails
                alt_pkg_id = f"PythonSoftwareFoundation.Python.{major_minor}"
                result = subprocess.run(
                    [
                        "winget",
                        "install",
                        "--id",
                        alt_pkg_id,
                        "--source",
                        "msstore",
                        "--accept-package-agreements",
                        "--accept-source-agreements",
                    ],
                    check=False,
                )
                if result.returncode == 0:
                    print(f"\n[OK] Python {major_minor} installed via Microsoft Store!")
                    return True

        except Exception as e:
            print(f"winget error: {e}")
        return False

    def uninstall(self, version: str) -> bool:
        parts = version.split(".")
        if len(parts) < 2:
            return False
        major_minor = f"{parts[0]}.{parts[1]}"

        try:
            pkg_id = f"Python.Python.{major_minor}"
            result = subprocess.run(["winget", "uninstall", "--id", pkg_id], check=False, capture_output=True)
            if result.returncode == 0:
                return True

            alt_pkg_id = f"PythonSoftwareFoundation.Python.{major_minor}"
            result = subprocess.run(["winget", "uninstall", "--id", alt_pkg_id], check=False, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False

    def get_priority(self) -> int:
        return 75  # Higher than standard Windows installer, lower than pyenv/mise


class SourceInstaller(InstallerPlugin):
    """Installer that builds Python from source (Linux)."""

    def get_name(self) -> str:
        return "source"

    def is_supported(self) -> bool:
        return platform.system() == "Linux"

    def install(self, version: str, **kwargs: Any) -> bool:
        print(f"⚙️ Preparing build environment for {version}...")

        # Ensure dependencies (simplified version of install_pyenv_linux logic)
        if not self._install_dependencies():
            return False

        source_url = f"https://www.python.org/ftp/python/{version}/Python-{version}.tar.xz"
        temp_dir = tempfile.gettempdir()
        source_path = os.path.join(temp_dir, f"Python-{version}.tar.xz")

        if not download_file(source_url, source_path):
            print("❌ Failed to download source code.")
            return False

        build_dir = os.path.join(temp_dir, f"Python-{version}")
        try:
            print("📦 Extracting and Compiling (this will take a few minutes)...")
            subprocess.run(["tar", "-xf", source_path, "-C", temp_dir], check=True)

            print(f"🔧 Configuring and building with {os.cpu_count() or 2} cores...")
            cpu_cores = str(os.cpu_count() or 2)

            configure_cmd = ["./configure"]
            if kwargs.get("optimizations", True):
                configure_cmd.append("--enable-optimizations")

            if kwargs.get("install_path"):
                configure_cmd.append(f"--prefix={kwargs['install_path']}")

            subprocess.run(configure_cmd, cwd=build_dir, check=True)
            subprocess.run(["make", f"-j{cpu_cores}"], cwd=build_dir, check=True)
            subprocess.run(["sudo", "make", "altinstall"], cwd=build_dir, check=True)

            return True
        except Exception as e:
            print(f"❌ Build failed: {e}")
            return False
        finally:
            if os.path.exists(build_dir):
                shutil.rmtree(build_dir, ignore_errors=True)
            if os.path.exists(source_path):
                os.remove(source_path)

    def uninstall(self, version: str) -> bool:
        # Source uninstallation is manual
        return False

    def get_priority(self) -> int:
        return 50

    def _install_dependencies(self) -> bool:
        """Install build dependencies on Linux."""
        if not shutil.which("curl") or not shutil.which("bash"):
            return False

        pkg_mgr = "dnf" if shutil.which("dnf") else "yum"
        if not shutil.which(pkg_mgr):
            if shutil.which("apt"):
                pkg_mgr = "apt"
            else:
                return False

        deps = []
        if pkg_mgr in ["dnf", "yum"]:
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
        elif pkg_mgr == "apt":
            deps = [
                "build-essential",
                "libssl-dev",
                "zlib1g-dev",
                "libncurses5-dev",
                "libncursesw5-dev",
                "libreadline-dev",
                "libsqlite3-dev",
                "libgdbm-dev",
                "libdb5.3-dev",
                "libbz2-dev",
                "libexpat1-dev",
                "liblzma-dev",
                "tk-dev",
                "libffi-dev",
            ]

        try:
            prefix = ["sudo"] if shutil.which("sudo") else []
            if pkg_mgr == "apt":
                subprocess.run(prefix + ["apt", "update"], check=True)
                subprocess.run(prefix + ["apt", "install", "-y"] + deps, check=True)
            else:
                subprocess.run(prefix + [pkg_mgr, "install", "-y"] + deps, check=True)
            return True
        except Exception as e:
            print(f"Error installing dependencies: {e}")
            return False


class CondaInstaller(InstallerPlugin):
    """Installer using Conda/Mamba."""

    def get_name(self) -> str:
        return "conda"

    def is_supported(self) -> bool:
        if shutil.which("conda") or shutil.which("mamba"):
            return True

        # On Windows, check common paths
        if platform.system() == "Windows":
            user_profile = os.environ.get("USERPROFILE", "")
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            common_paths = [
                Path(user_profile) / "miniconda3" / "Scripts" / "conda.exe",
                Path(user_profile) / "anaconda3" / "Scripts" / "conda.exe",
                Path("C:/ProgramData/miniconda3/Scripts/conda.exe"),
                Path("C:/ProgramData/anaconda3/Scripts/conda.exe"),
                Path("D:/miniconda3/Scripts/conda.exe"),
                Path("D:/anaconda3/Scripts/conda.exe"),
                Path(local_appdata) / "miniconda3" / "Scripts" / "conda.exe",
                Path(local_appdata) / "anaconda3" / "Scripts" / "conda.exe",
            ]
            for path in common_paths:
                if path.exists():
                    return True
        return False

    def _get_exe(self) -> str:
        """Get the executable path for conda/mamba."""
        if shutil.which("mamba"):
            return "mamba"
        if shutil.which("conda"):
            return "conda"

        if platform.system() == "Windows":
            user_profile = os.environ.get("USERPROFILE", "")
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            common_paths = [
                Path(user_profile) / "miniconda3" / "Scripts" / "conda.exe",
                Path(user_profile) / "anaconda3" / "Scripts" / "conda.exe",
                Path("C:/ProgramData/miniconda3/Scripts/conda.exe"),
                Path("C:/ProgramData/anaconda3/Scripts/conda.exe"),
                Path("D:/miniconda3/Scripts/conda.exe"),
                Path("D:/anaconda3/Scripts/conda.exe"),
                Path(local_appdata) / "miniconda3" / "Scripts" / "conda.exe",
                Path(local_appdata) / "anaconda3" / "Scripts" / "conda.exe",
            ]
            for path in common_paths:
                if path.exists():
                    return str(path)
        return "conda"

    def install(self, version: str, **kwargs: Any) -> bool:
        exe = self._get_exe()
        print(f"Using {exe} to install Python {version}...")
        try:
            # Conda installs into environments. We'll create one named pyvm-<version>
            env_name = f"pyvm-{version}"
            result = subprocess.run(
                [exe, "create", "-y", "-n", env_name, f"python={version}"],
                check=False,
            )
            if result.returncode == 0:
                print(f"\n[OK] Python {version} installed via {exe} in environment: {env_name}")
                print(f"To use: {exe} activate {env_name}")
                return True
        except Exception as e:
            print(f"{exe} error: {e}")
        return False

    def uninstall(self, version: str) -> bool:
        exe = self._get_exe()
        try:
            env_name = f"pyvm-{version}"
            result = subprocess.run(
                [exe, "env", "remove", "-y", "-n", env_name],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_priority(self) -> int:
        return 85


class AsdfInstaller(InstallerPlugin):
    """Installer using asdf."""

    def get_name(self) -> str:
        return "asdf"

    def is_supported(self) -> bool:
        return bool(shutil.which("asdf"))

    def install(self, version: str, **kwargs: Any) -> bool:
        print(f"Using asdf to install Python {version}...")
        try:
            # Ensure python plugin is installed
            subprocess.run(
                ["asdf", "plugin", "add", "python"],
                check=False,
                capture_output=True,
            )

            result = subprocess.run(["asdf", "install", "python", version], check=False)
            if result.returncode == 0:
                print(f"\n[OK] Python {version} installed via asdf!")
                print(f"To use: asdf global python {version}")
                return True
        except Exception as e:
            print(f"asdf error: {e}")
        return False

    def uninstall(self, version: str) -> bool:
        try:
            result = subprocess.run(
                ["asdf", "uninstall", "python", version],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_priority(self) -> int:
        return 95
