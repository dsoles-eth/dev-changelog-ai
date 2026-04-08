import pytest
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock, PropertyMock, call
from pathlib import Path

import commit_parser
from commit_parser import (
    CommitHistoryParser,
    ParsedCommit,
    CommitParseError,
    RepositoryError,
    COMMIT_REGEX
)


# Fixture for a generic datetime instance
@pytest.fixture
def sample_datetime():
    return datetime(2023, 1, 15, 10, 0, 0)


# Fixture for a mocked git.Commit object
@pytest.fixture
def mock_git_commit(sample_datetime):
    commit = MagicMock()
    commit.hexsha = "a1b2c3d4e5f6g7h8i9j0"
    commit.author.name = "John Doe"
    commit.author.email = "john.doe@example.com"
    commit.committed_datetime = sample_datetime
    commit.message = "feat: add new feature\n\nThis is the body."
    return commit


# Fixture to patch the git module before accessing commit_parser
@pytest.fixture(autouse=True)
def patch_git_module():
    with patch("commit_parser.git") as mock_git:
        # Setup git exceptions
        mock_git.InvalidGitRepositoryError = Exception("InvalidRepository")
        mock