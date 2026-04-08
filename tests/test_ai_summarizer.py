import sys
from unittest import mock

import pytest
from ai_summarizer import summarize_commits, group_commits, build_prompt

SAMPLE_COMMITS = [
    {"hash": "a1b2c3", "message": "feat: add user login"},
    {"hash": "d4e5f6", "message": "fix: resolve login timeout"},
    {"hash": "g7h8i9", "message": "docs: update readme"},
]

VALID_API_KEY = "test-key-12345"
LLM_RESPONSE = "## Features\n- User login feature added\n## Fixes\n- Login timeout issue resolved"


@pytest.fixture
def mock_requests():
    with mock.patch.object(
        sys.modules.get("ai_summarizer", None) or mock.MagicMock(),
        "requests",
    ) as mock_requests:
        yield mock_requests


@pytest.fixture
def mock_requests_post():
    with mock.patch("ai_summarizer.requests.post") as mock_post:
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"text": LLM_RESPONSE}]}
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def commits():
    return SAMPLE_COMMITS


class TestGroupCommits:
    def test_group_commits_by_type(self, commits, mock_requests_post):
        result = group_commits(commits, group_keys=["type"])
        assert "feat" in result
        assert "fix" in result
        assert "docs" in result
        mock_requests_post.assert_not_called()

    def test_group_commits_by_scope(self, commits, mock_requests_post):
        test_commits = [
            {"hash": "1", "message": "feat(auth): login"},
            {"hash": "2", "message": "feat(api): endpoint"},
        ]
        result = group_commits(test_commits, group_keys=["scope"])
        assert "auth" in result
        assert "api" in result
        mock_requests_post.assert_not_called()

    def test_group_commits_empty_list(self, commits, mock_requests_post):
        result = group_commits([], group_keys=["type"])
        assert result == {}
        mock_requests_post.assert_not_called()


class TestSummarizeCommits:
    @mock.patch("ai_summarizer.requests.post")
    def test_summarize_commits_happy_path(self, mock_post, commits, mock_requests_post):
        mock_post.return_value = mock.MagicMock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"text": "Summary text here"}]
        }
        result = summarize_commits(commits, VALID_API_KEY)
        assert "Summary text here" in result
        mock_post.assert_called_once()

    @mock.patch("ai_summarizer.requests.post")
    def test_summarize_commits_api_error(self, mock_post, commits):
        mock_post.side_effect = Exception("API Connection Failed")
        with pytest.raises(Exception) as exc_info:
            summarize_commits(commits, VALID_API_KEY)
        assert "API Connection Failed" in str(exc_info.value)
        mock_post.assert_called_once()

    @mock.patch("ai_summarizer.requests.post")
    def test_summarize_commits_empty_commits(self, mock_post, commits):
        mock_post.return_value = mock.MagicMock()
        mock_post.return_value.status_code = 200
        mock_post.return_value.json