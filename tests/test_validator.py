import pytest
import validator
from unittest.mock import patch, MagicMock


# Fixtures for test data
@pytest.fixture
def valid_semver():
    return "1.0.0"


@pytest.fixture
def valid_semver_pre_release():
    return "2.1.0-beta.1"


@pytest.fixture
def invalid_semver():
    return "1.0"


@pytest.fixture
def valid_changelog_entry():
    return "- Fixed: Login bug (v1.0.0)"


@pytest.fixture
def invalid_changelog_entry():
    return "Login bug fixed"


@pytest.fixture
def valid_changelog_body():
    return """
# Changelog

## [1.0.0] - 2023-01-01
- Fixed: Login bug
"""


@pytest.fixture
def invalid_changelog_body():
    return """
# Changelog

[1.0.0] - 2023-01-01
Fixed: Login bug
"""


@pytest.fixture
def mock_api_response():
    return MagicMock(return_value={"status": "active", "version": "1.0.1"})


# Tests for semantic versioning validation
class TestValidatorSemanticVersion:

    def test_validate_semver_valid_version(self, valid_semver):
        result = validator.validate_semver(valid_semver)
        assert result is True

    def test_validate_semver_invalid_version_format(self, invalid_semver):
        with pytest.raises(ValueError):
            validator.validate_semver(invalid_semver)

    def test_validate_semver_with_prerelease(self, valid_semver_pre_release):
        result = validator.validate_semver(valid_semver_pre_release)
        assert result is True


# Tests for changelog format validation
class TestValidatorChangelogFormat:

    def test_validate_entry_valid_structure(self, valid_changelog_entry):
        result = validator.validate_changelog_entry(valid_changelog_entry)
        assert result is True

    def test_validate_entry_missing_type(self, invalid_changelog_entry):
        result = validator.validate_changelog_entry(invalid_changelog_entry)
        assert result is False

    def test_validate_body_valid_format(self, valid_changelog_body):
        result = validator.validate_changelog_content(valid_changelog_body)
        assert result is True


# Tests for external API integration
class TestValidatorAPIIntegration:

    @patch('validator.requests.get')
    def test_fetch_version_info_success(self, mock_get, mock_api_response):
        mock_get.return_value.json.return_value = mock_api_response
        result = validator.get_version_info("https://api.example.com/version")
        assert result["version"] == "1.0.1"
        mock_get.assert_called_once_with("https://api.example.com/version")

    @patch('validator.requests.get')
    def test_fetch_version_info_network_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        with pytest.raises(Exception):
            validator.get_version_info("https://api.example.com/version")

    @patch('validator.requests.get')
    def test_fetch_version_info_invalid_json(self, mock_get):
        mock_get.return_value.json.side_effect = ValueError("Invalid JSON")
        with pytest.raises(ValueError):
            validator.get_version_info("https://api.example.com/version")


# Tests for validation flow combination
class TestValidatorFullFlow:

    def test_flow_validate_version_and_entry(self, valid_semver, valid_changelog_entry):
        is_semver = validator.validate_semver(valid_semver)
        is_entry = validator.validate_changelog_entry(valid_changelog_entry)
        assert is_semver is True
        assert is_entry is True

    def test_flow_with_invalid_input(self, invalid_semver, invalid_changelog_entry):
        is_semver = validator.validate_semver(invalid_semver)
        is_entry = validator.validate_changelog_entry(invalid_changelog_entry)
        assert is_semver is False
        assert is_entry is False

    def test_flow_integration_with_api_patch(self):
        with patch.object(validator, 'get_version_info', return_value={"status": "ok"}):
            status = validator.check_repository_status()
            assert status is not None