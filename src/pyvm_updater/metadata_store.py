from __future__ import annotations

import sqlite3
import threading
import time
from typing import Any

import requests  # type: ignore
from bs4 import BeautifulSoup

from .constants import MAX_RETRIES, METADATA_DB, METADATA_TTL_SECONDS, REQUEST_TIMEOUT, RETRY_DELAY
from .utils import validate_version_string


def _connect() -> sqlite3.Connection:
    METADATA_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(METADATA_DB))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS series (series TEXT PRIMARY KEY, status TEXT, first_release TEXT, end_of_support TEXT, latest_version TEXT, source TEXT, fetched_at INTEGER)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS versions (version TEXT PRIMARY KEY, url TEXT, source TEXT, fetched_at INTEGER)"
    )
    conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    return conn


def _now() -> int:
    return int(time.time())


def is_cache_stale() -> bool:
    try:
        with _connect() as conn:
            cur = conn.execute("SELECT value FROM meta WHERE key='last_sync'")
            row = cur.fetchone()
            if not row:
                return True
            last_sync = int(row[0])
            return (_now() - last_sync) > METADATA_TTL_SECONDS
    except Exception:
        return True


def get_releases_from_cache() -> list[dict[str, Any]]:
    try:
        with _connect() as conn:
            cur = conn.execute(
                "SELECT series, status, first_release, end_of_support, latest_version FROM series ORDER BY series DESC"
            )
            rows = cur.fetchall()
            return [
                {
                    "series": r[0],
                    "status": r[1],
                    "first_release": r[2],
                    "end_of_support": r[3],
                    "latest_version": r[4],
                }
                for r in rows
            ]
    except Exception:
        return []


def get_versions_from_cache(limit: int = 50) -> list[dict[str, str]]:
    try:
        with _connect() as conn:
            cur = conn.execute("SELECT version, url FROM versions ORDER BY fetched_at DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return [{"version": r[0], "url": r[1]} for r in rows]
    except Exception:
        return []


def sync_python_org() -> None:
    url = "https://www.python.org/downloads/"
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text()
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            start_idx = None
            for i, line in enumerate(lines):
                if line == "Release schedule":
                    start_idx = i + 1
                    break
            releases: list[dict[str, Any]] = []
            if start_idx:
                i = start_idx
                while i < len(lines) - 5:
                    line = lines[i]
                    if validate_version_string(line) and line.count(".") == 1:
                        series = line
                        status = lines[i + 1] if i + 1 < len(lines) else ""
                        first_release = lines[i + 3] if i + 3 < len(lines) else ""
                        end_support = lines[i + 4] if i + 4 < len(lines) else ""
                        if status and not status.startswith("Looking for"):
                            releases.append(
                                {
                                    "series": series,
                                    "status": status,
                                    "first_release": first_release,
                                    "end_of_support": end_support,
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
            with _connect() as conn:
                conn.execute("BEGIN")
                try:
                    for rel in releases:
                        lv = series_versions.get(rel["series"])
                        conn.execute(
                            "INSERT OR REPLACE INTO series(series, status, first_release, end_of_support, latest_version, source, fetched_at) VALUES(?,?,?,?,?,?,?)",
                            (
                                rel["series"],
                                rel["status"],
                                rel["first_release"],
                                rel["end_of_support"],
                                lv,
                                "python.org",
                                _now(),
                            ),
                        )
                    conn.execute(
                        "INSERT OR REPLACE INTO meta(key, value) VALUES('last_sync', ?)",
                        (str(_now()),),
                    )
                    release_links = soup.find_all("span", class_="release-number")
                    for release in release_links[:200]:
                        link = release.find("a")
                        if link:
                            vt = link.get_text(strip=True)
                            if vt.startswith("Python "):
                                ver = vt.replace("Python ", "")
                                if validate_version_string(ver):
                                    href_val = link.get("href")
                                    if isinstance(href_val, str):
                                        full = (
                                            f"https://www.python.org{href_val}"
                                            if not href_val.startswith("http")
                                            else href_val
                                        )
                                    else:
                                        full = ""
                                    conn.execute(
                                        "INSERT OR REPLACE INTO versions(version, url, source, fetched_at) VALUES(?,?,?,?)",
                                        (ver, full, "python.org", _now()),
                                    )
                    conn.execute("COMMIT")
                except Exception:
                    conn.execute("ROLLBACK")
                    raise
            return
        except Exception:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                return


_sync_lock = threading.Lock()


def start_background_sync_if_stale() -> None:
    if not is_cache_stale():
        return
    if _sync_lock.locked():
        return

    def _run():
        try:
            _sync_lock.acquire()
            sync_python_org()
        finally:
            try:
                _sync_lock.release()
            except Exception:
                pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()
