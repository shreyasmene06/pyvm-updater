"""Tests for pyvm_updater.utils module."""

import requests

from pyvm_updater.utils import (
    fetch_remote_sha256,
    get_os_info,
    validate_version_string,
    verify_file_checksum,
)



class TestValidateVersionString:
    """Tests for validate_version_string function."""

    def test_valid_major_minor_patch(self):
        """Test valid X.Y.Z format."""
        assert validate_version_string("3.11.5") is True
        assert validate_version_string("3.12.1") is True
        assert validate_version_string("2.7.18") is True

    def test_valid_major_minor(self):
        """Test valid X.Y format."""
        assert validate_version_string("3.11") is True
        assert validate_version_string("3.9") is True

    def test_valid_extended_version(self):
        """Test valid X.Y.Z.A format."""
        assert validate_version_string("3.11.5.1") is True

    def test_invalid_empty_string(self):
        """Test empty string returns False."""
        assert validate_version_string("") is False

    def test_invalid_single_number(self):
        """Test single number is invalid."""
        assert validate_version_string("3") is False

    def test_invalid_text(self):
        """Test text strings are invalid."""
        assert validate_version_string("latest") is False
        assert validate_version_string("stable") is False

    def test_invalid_with_letters(self):
        """Test versions with letters are invalid."""
        assert validate_version_string("3.11.5a") is False
        assert validate_version_string("3.11rc1") is False

    def test_invalid_with_special_chars(self):
        """Test versions with special characters are invalid."""
        assert validate_version_string("3.11-5") is False
        assert validate_version_string("3.11_5") is False



class TestGetOsInfo:
    """Tests for get_os_info function."""

    def test_returns_tuple(self):
        """Test that get_os_info returns a tuple."""
        result = get_os_info()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_os_name_is_lowercase(self):
        """Test that OS name is lowercase."""
        os_name, _ = get_os_info()
        assert os_name == os_name.lower()

    def test_arch_is_normalized(self):
        """Test that architecture is normalized to amd64, arm64, or x86."""
        _, arch = get_os_info()
        assert arch in ["amd64", "arm64", "x86"]



class TestFetchRemoteSha256:
    """Tests for fetch_remote_sha256 — all network I/O is mocked."""

    def test_network_timeout_returns_none(self, mocker):
        """A network timeout must be caught and return None gracefully."""
        mocker.patch(
            "pyvm_updater.utils.requests.get",
            side_effect=requests.exceptions.Timeout("timed out"),
        )
        result = fetch_remote_sha256("https://example.com/checksum.txt")
        assert result is None

    def test_http_error_returns_none(self, mocker):
        """An HTTP error (e.g. 404 / 500) must be caught and return None safely."""
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        mocker.patch("pyvm_updater.utils.requests.get", return_value=mock_response)

        result = fetch_remote_sha256("https://example.com/checksum.txt")
        assert result is None

    def test_whitespace_only_body_returns_none(self, mocker):
        """A response body containing only whitespace must return None after stripping."""
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "   \n\t  "
        mocker.patch("pyvm_updater.utils.requests.get", return_value=mock_response)

        result = fetch_remote_sha256("https://example.com/checksum.txt")
        assert result is None

    def test_malformed_string_returns_none(self, mocker):
        """A string that is not exactly 64 hex characters must fail the regex and return None."""
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status.return_value = None
        # Simulating a payload that isn't a valid SHA-256 hash
        mock_response.text = "invalid_hash_string_that_is_too_short" 
        mocker.patch("pyvm_updater.utils.requests.get", return_value=mock_response)

        result = fetch_remote_sha256("https://example.com/checksum.txt")
        assert result is None
    
    def test_valid_response_returns_hash(self, mocker):
        """A well-formed checksum file returns only the hash token."""
        fake_hash = "a" * 64
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = f"{fake_hash}  Python-3.12.0.tgz\n"
        mocker.patch("pyvm_updater.utils.requests.get", return_value=mock_response)

        result = fetch_remote_sha256("https://example.com/checksum.txt")
        assert result == fake_hash



class TestVerifyFileChecksum:
    """Tests for verify_file_checksum — network and config are fully mocked."""

    def test_failed_remote_fetch_returns_false(self, mocker):
        """If the remote hash fetch fails (returns None), integrity check must return False."""
        mocker.patch("pyvm_updater.utils.fetch_remote_sha256", return_value=None)
        mock_cfg = mocker.MagicMock()
        mock_cfg.verify_checksum = True
        mocker.patch("pyvm_updater.config.get_config", return_value=mock_cfg)

        result = verify_file_checksum("/fake/path/file.tar.gz", "https://example.com/sha256")
        assert result is False

    def test_mismatched_hashes_returns_false(self, mocker):
        """Local hash that differs from the remote hash must return False."""
        mocker.patch("pyvm_updater.utils.fetch_remote_sha256", return_value="a" * 64)
        mocker.patch("pyvm_updater.utils.calculate_sha256", return_value="b" * 64)
        mock_cfg = mocker.MagicMock()
        mock_cfg.verify_checksum = True
        mocker.patch("pyvm_updater.config.get_config", return_value=mock_cfg)

        result = verify_file_checksum("/fake/path/file.tar.gz", "https://example.com/sha256")
        assert result is False

    def test_matching_hashes_returns_true(self, mocker):
        """Matching local and remote hashes must return True (standard happy path)."""
        good_hash = "c" * 64
        mocker.patch("pyvm_updater.utils.fetch_remote_sha256", return_value=good_hash)
        mocker.patch("pyvm_updater.utils.calculate_sha256", return_value=good_hash)
        mock_cfg = mocker.MagicMock()
        mock_cfg.verify_checksum = True
        mocker.patch("pyvm_updater.config.get_config", return_value=mock_cfg)

        result = verify_file_checksum("/fake/path/file.tar.gz", "https://example.com/sha256")
        assert result is True

    def test_disabled_config_skips_check(self, mocker):
        """When verify_checksum is False in config, the check must be bypassed and return True."""
        fetch_spy = mocker.patch("pyvm_updater.utils.fetch_remote_sha256")
        mock_cfg = mocker.MagicMock()
        mock_cfg.verify_checksum = False
        mocker.patch("pyvm_updater.config.get_config", return_value=mock_cfg)

        result = verify_file_checksum("/fake/path/file.tar.gz", "https://example.com/sha256")
        assert result is True
        fetch_spy.assert_not_called()
