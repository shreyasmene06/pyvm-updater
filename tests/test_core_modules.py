"""Tests for config.py, logging_config.py, and metadata_store.py."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from pyvm_updater.config import DEFAULT_CONFIG, Config
from pyvm_updater.logging_config import get_logger, setup_logging
from pyvm_updater.metadata_store import _connect, _now, is_cache_stale


class TestConfig:
    def setup_method(self):
        Config._instance = None
        Config._config = DEFAULT_CONFIG.copy()

    def teardown_method(self):
        Config._instance = None

    def test_singleton(self):
        c1 = Config()
        c2 = Config()
        assert c1 is c2

    def test_get_default_value(self):
        cfg = Config()
        assert cfg.get("general", "auto_confirm") is False

    def test_get_missing_key_returns_default(self):
        cfg = Config()
        assert cfg.get("general", "nonexistent", "fallback") == "fallback"

    def test_set_value(self):
        cfg = Config()
        cfg.set("general", "verbose", True)
        assert cfg.get("general", "verbose") is True

    def test_set_creates_new_section(self):
        cfg = Config()
        cfg.set("custom", "key", "value")
        assert cfg.get("custom", "key") == "value"

    def test_auto_confirm_property(self):
        cfg = Config()
        assert cfg.auto_confirm is False
        cfg.set("general", "auto_confirm", True)
        assert cfg.auto_confirm is True

    def test_verbose_property(self):
        cfg = Config()
        cfg.set("general", "verbose", False)
        assert cfg.verbose is False

    def test_preferred_installer_property(self):
        cfg = Config()
        assert cfg.preferred_installer == "auto"

    def test_verify_checksum_property(self):
        cfg = Config()
        assert cfg.verify_checksum is True

    def test_max_retries_property(self):
        cfg = Config()
        assert cfg.max_retries == 3

    def test_download_timeout_property(self):
        cfg = Config()
        assert cfg.download_timeout == 120

    def test_tui_theme_property(self):
        cfg = Config()
        assert cfg.tui_theme == "dark"

    def test_save_and_load(self):
        Config._instance = None
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.toml"
            with patch("pyvm_updater.config.CONFIG_FILE", config_file), patch(
                "pyvm_updater.config.CONFIG_DIR", Path(tmp)
            ):
                cfg = Config()
                cfg.set("general", "verbose", True)
                assert cfg.save() is True

                Config._instance = None
                cfg2 = Config()
                cfg2._config = DEFAULT_CONFIG.copy()
                cfg2._load()
                assert cfg2.get("general", "verbose") is True

    def test_save_handles_bool_and_string(self):
        Config._instance = None
        with tempfile.TemporaryDirectory() as tmp:
            config_file = Path(tmp) / "config.toml"
            with patch("pyvm_updater.config.CONFIG_FILE", config_file), patch(
                "pyvm_updater.config.CONFIG_DIR", Path(tmp)
            ):
                cfg = Config()
                cfg.set("general", "auto_confirm", False)
                result = cfg.save()
                assert result is True
                content = config_file.read_text()
                assert "auto_confirm = false" in content

    def test_merge_config_new_section(self):
        cfg = Config()
        cfg._merge_config({"new_section": {"key": "val"}})
        assert cfg.get("new_section", "key") == "val"

    def test_merge_config_updates_existing(self):
        cfg = Config()
        cfg._merge_config({"general": {"verbose": True}})
        assert cfg.get("general", "verbose") is True


class TestLoggingConfig:
    def test_setup_default_level(self):
        logger = setup_logging()
        assert logger.level == logging.INFO

    def test_setup_verbose_level(self):
        logger = setup_logging(verbose=True)
        assert logger.level == logging.DEBUG

    def test_setup_quiet_level(self):
        logger = setup_logging(quiet=True)
        assert logger.level == logging.WARNING

    def test_get_logger_with_name(self):
        logger = get_logger("test")
        assert logger.name == "pyvm.test"

    def test_get_logger_without_name(self):
        logger = get_logger()
        assert logger.name == "pyvm"

    def test_setup_clears_old_handlers(self):
        setup_logging()
        setup_logging()
        logger = logging.getLogger("pyvm")
        assert len(logger.handlers) == 1


class TestMetadataStore:
    def test_connect_creates_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            with patch("pyvm_updater.metadata_store.METADATA_DB", db_path):
                conn = _connect()
                cur = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = {row[0] for row in cur.fetchall()}
                assert "series" in tables
                assert "versions" in tables
                assert "meta" in tables
                conn.close()

    def test_is_cache_stale_when_no_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "nonexistent.db"
            with patch("pyvm_updater.metadata_store.METADATA_DB", db_path):
                assert is_cache_stale() is True

    def test_is_cache_stale_when_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            with patch("pyvm_updater.metadata_store.METADATA_DB", db_path):
                conn = _connect()
                conn.execute(
                    "INSERT INTO meta(key, value) VALUES('last_sync', ?)",
                    (str(_now()),),
                )
                conn.commit()
                conn.close()
                assert is_cache_stale() is False

    def test_is_cache_stale_when_old(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            with patch("pyvm_updater.metadata_store.METADATA_DB", db_path):
                conn = _connect()
                old_time = _now() - 999999
                conn.execute(
                    "INSERT INTO meta(key, value) VALUES('last_sync', ?)",
                    (str(old_time),),
                )
                conn.commit()
                conn.close()
                assert is_cache_stale() is True

    @patch("pyvm_updater.metadata_store.requests.get")
    def test_sync_writes_to_db(self, mock_get):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            with patch("pyvm_updater.metadata_store.METADATA_DB", db_path):
                mock_get.return_value = MagicMock(
                    status_code=200,
                    text="<html><body><span class='release-number'><a href='/downloads/'>Python 3.12.0</a></span></body></html>",
                )
                mock_get.return_value.raise_for_status = MagicMock()

                from pyvm_updater.metadata_store import sync_python_org

                sync_python_org()

                conn = _connect()
                cur = conn.execute("SELECT COUNT(*) FROM versions")
                count = cur.fetchone()[0]
                conn.close()
                assert count >= 1
