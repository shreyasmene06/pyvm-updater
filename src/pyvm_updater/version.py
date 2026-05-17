"""Version checking and fetching logic for pyvm_updater."""

from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
import time
from typing import Any

import requests  # type: ignore
from bs4 import BeautifulSoup
from packaging import version as pkg_version

from .constants import MAX_RETRIES, REQUEST_TIMEOUT, RETRY_DELAY
from .metadata_store import (
    get_releases_from_cache,
    get_versions_from_cache,
    start_background_sync_if_stale,
    sync_python_org,
)
from .utils import get_os_info, validate_version_string


def get_installed_python_versions() -> list[dict[str, Any]]:
    """Detect Python versions installed on the system."""
    versions: list[dict[str, Any]] = []
    os_name, _ = get_os_info()
    found: set[str] = set()

    if os_name == "windows":
        try:
            result = subprocess.run(["py", "--list"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    line = line.strip()
                    match = re.search(r"-(?:V:)?(\d+\.\d+)", line)
                    if match:
                        ver = match.group(1)
                        is_default = "*" in line
                        is_store = "(Store)" in line
                        if ver not in found:
                            found.add(ver)
                            versions.append(
                                {
                                    "version": ver,
                                    "path": None,
                                    "default": is_default,
                                    "store": is_store,
                                }
                            )
        except FileNotFoundError:
            pass

        # Explicitly check for Store versions if py --list didn't catch them or to get paths
        try:
            # Check %LOCALAPPDATA%\Microsoft\WindowsApps for python3.x.exe
            apps_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps")
            if os.path.isdir(apps_dir):
                for entry in os.listdir(apps_dir):
                    match = re.match(r"python(3\.\d+)\.exe", entry, re.IGNORECASE)
                    if match:
                        ver = match.group(1)
                        if ver not in found:
                            found.add(ver)
                            full_path = os.path.join(apps_dir, entry)
                            versions.append(
                                {
                                    "version": ver,
                                    "path": full_path,
                                    "default": full_path == sys.executable,
                                    "store": True,
                                }
                            )
                        else:
                            # Update existing entry with path if it's a store version
                            for v in versions:
                                if v["version"] == ver:
                                    v["store"] = True
                                    if not v["path"]:
                                        v["path"] = os.path.join(apps_dir, entry)
                                    break
        except Exception:
            pass
    else:
        # mise
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

        # pyenv
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

        # system paths
        search_paths = [
            "/usr/bin",
            "/usr/local/bin",
            "/opt/homebrew/bin",
            os.path.expanduser("~/.local/bin"),
        ]
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
                                if os.access(full_path, os.X_OK):
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

    def version_key(x: dict[str, Any]) -> list[int]:
        try:
            return [int(p) for p in x["version"].split(".")[:3]]
        except ValueError:
            return [0, 0, 0]

    versions.sort(key=version_key, reverse=True)

    current_ver = platform.python_version()
    found_current = any(v["version"] == current_ver for v in versions)

    if not found_current:
        versions.insert(0, {"version": current_ver, "path": sys.executable, "default": True})
    else:
        for v in versions:
            if v["version"] == current_ver:
                v["default"] = True
                break

    return versions


def get_latest_python_info_with_retry() -> tuple[str | None, str | None]:
    """Fetch the latest Python version with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            result = get_latest_python_info()
            if result[0]:
                return result
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                print(f"All retry attempts failed: {e}")
    return None, None


def get_latest_python_info() -> tuple[str | None, str | None]:
    """Fetch the latest Python version and download URLs."""
    URL = "https://www.python.org/downloads/"

    try:
        response = requests.get(URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        download_button = soup.find("a", class_="button")
        if not download_button:
            print("Error: Could not find download button on Python.org")
            return None, None

        latest_ver_string = download_button.get_text(strip=True)
        latest_ver = latest_ver_string.split()[-1]

        if not validate_version_string(latest_ver):
            print(f"Error: Invalid version format retrieved: {latest_ver}")
            return None, None

        download_url_raw = download_button.get("href")
        download_url: str | None = None
        if download_url_raw and isinstance(download_url_raw, str):
            if not download_url_raw.startswith("http"):
                download_url = f"https://www.python.org{download_url_raw}"
            else:
                download_url = download_url_raw

        return latest_ver, download_url

    except requests.Timeout:
        print("Error: Request to python.org timed out.")
        return None, None
    except requests.RequestException as e:
        print(f"Error: Network request failed: {e}")
        return None, None
    except Exception as e:
        print(f"Error: Unexpected error: {e}")
        return None, None


def get_active_python_releases() -> list[dict[str, Any]]:
    cached = get_releases_from_cache()
    if cached:
        start_background_sync_if_stale()
        return cached
    try:
        sync_python_org()
        data = get_releases_from_cache()
        if data:
            return data
    except Exception:
        pass
    try:
        return _fetch_active_python_releases_fallback()
    except Exception:
        return []


def _fetch_active_python_releases_fallback() -> list[dict[str, Any]]:
    url = "https://www.python.org/downloads/"
    releases: list[dict[str, Any]] = []
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text()
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    start_idx = None
    for i, line in enumerate(lines):
        if line == "Release schedule":
            start_idx = i + 1
            break
    if start_idx:
        i = start_idx
        while i < len(lines) - 5:
            line = lines[i]
            if re.match(r"^\d+\.\d+$", line):
                series = line
                status = lines[i + 1] if i + 1 < len(lines) else ""
                first_release = lines[i + 3] if i + 3 < len(lines) else ""
                end_support = lines[i + 4] if i + 4 < len(lines) else ""
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
                i += 6
            else:
                i += 1
    release_links = soup.find_all("span", class_="release-number")
    series_versions: dict[str, str] = {}
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
                        series_versions.setdefault(series, ver)
    for rel in releases:
        if rel["series"] in series_versions:
            rel["latest_version"] = series_versions[rel["series"]]
    return releases


def get_available_python_versions(limit: int = 50) -> list[dict[str, str]]:
    cached = get_versions_from_cache(limit)
    if cached:
        start_background_sync_if_stale()
        return cached
    try:
        sync_python_org()
        data = get_versions_from_cache(limit)
        if data:
            return data
    except Exception:
        pass
    try:
        url = "https://www.python.org/downloads/"
        versions: list[dict[str, str]] = []
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        release_links = soup.find_all("span", class_="release-number")
        for release in release_links[:limit]:
            link = release.find("a")
            if link:
                version_text = link.get_text(strip=True)
                if version_text.startswith("Python "):
                    ver = version_text.replace("Python ", "")
                    if validate_version_string(ver):
                        href_val = link.get("href")
                        if isinstance(href_val, str):
                            full = f"https://www.python.org{href_val}" if not href_val.startswith("http") else href_val
                        else:
                            full = ""
                        versions.append({"version": ver, "url": full})
        return versions
    except Exception:
        return []


def check_python_version(silent: bool = False) -> tuple[str, str | None, bool]:
    """Check local Python version against the latest stable version from python.org."""
    local_ver = platform.python_version()

    if not silent:
        print(f"Checking Python version... (Current: {local_ver})")

    latest_ver, _ = get_latest_python_info_with_retry()

    if not latest_ver:
        if not silent:
            print("Error: Could not fetch latest version information.")
        return local_ver, None, False

    try:
        if not validate_version_string(latest_ver):
            if not silent:
                print(f"Error: Invalid version format from server: {latest_ver}")
            return local_ver, None, False

        local_version_obj = pkg_version.parse(local_ver)
        latest_version_obj = pkg_version.parse(latest_ver)
        needs_update = local_version_obj < latest_version_obj

        if not silent:
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
        return local_ver, latest_ver, False


def is_python_version_installed(version_str: str) -> bool:
    """Check if a specific Python version is installed on the system."""
    installed = get_installed_python_versions()

    if any(v["version"] == version_str for v in installed):
        return True

    try:
        parts = version_str.split(".")
        if len(parts) >= 2:
            major_minor = f"{parts[0]}.{parts[1]}"
            return any(v["version"] == major_minor for v in installed)
    except (ValueError, IndexError):
        pass

    return False


def _normalize_status(text: str) -> str:
    t = text.lower()
    if t == "pre-release" or t== "prerelease" or t.startswith ("pre"-):
        return "prerelease"
    if "bugfix" in t or "active" in t:
        return "active"
    if "security" in t:
        return "security"
    if "end of life" in t or "eol" in t:
        return "eol"
    return t


def is_version_security_supported(ver: str) -> bool:
    try:
        parts = ver.split(".")
        if len(parts) < 2:
            return False
        series = f"{parts[0]}.{parts[1]}"
        for rel in get_active_python_releases():
            if rel.get("series") == series:
                status = _normalize_status(str(rel.get("status", "")))
                return status in {"security", "active"}
        return False
    except Exception:
        return False


def get_versions_filtered(
    min_version: str | None = None, security_supported_only: bool = False
) -> list[dict[str, Any]]:
    releases = get_active_python_releases()
    out: list[dict[str, Any]] = []
    for rel in releases:
        version = rel.get("latest_version")
        if not version or not validate_version_string(str(version)):
            continue
        if min_version:
            try:
                if pkg_version.parse(str(version)) < pkg_version.parse(min_version):
                    continue
            except Exception:
                pass
        status = _normalize_status(str(rel.get("status", "")))
        if security_supported_only and status not in {"security", "active"}:
            continue
        out.append({"version": str(version), "status": status})
    return out
