import pytest
from unittest.mock import patch, Mock, MagicMock, call
import subprocess
import git_integration


class MockCompletedProcess:
    def __init__(self, returncode=0, stdout=""):
        self.returncode = returncode
        self.stdout = stdout


class MockCalledProcessError(subprocess.CalledProcessError):
    def __init__(self, cmd=None, output=None, returncode=None, stderr=None):
        self.cmd = cmd
        self.output = output
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(returncode, cmd)


@pytest.fixture
def mock_git_success():
    mock_process = MockCompletedProcess(returncode=0, stdout="Success")
    return mock_process


@pytest.fixture
def mock_git_failure():
    mock_process = MockCalledProcessError(
        cmd=["git", "commit", "-m", "test"],
        returncode=1,
        stderr="Not a git repository"
    )
    return mock_process


@pytest.fixture
def mock_git_auth_failure():
    mock_process = MockCalledProcessError(
        cmd=["git", "push"],
        returncode=1,
        stderr="Permission denied"
    )
    return mock_process


class TestCreateCommit:
    @patch('git_integration.subprocess.run')
    def test_create_commit_success(self, mock_run, mock_git_success):
        mock_run.return_value = mock_git_success
        result = git_integration.create_commit("fix: bug in parser")
        mock_run.assert_called_once_with(
            ['git', 'commit', '-m', 'fix: bug in parser'],
            capture_output=True,
            check=False
        )
        assert result is True

    @patch('git_integration.subprocess.run')
    def test_create_commit_multiple_messages(self, mock_run, mock_git_success):
        mock_run.return_value = mock_git_success
        result = git_integration.create_commit("feat: new feature", versioned=True)
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert 'feat:' in call_args or 'feat' in ' '.join(call_args)
        assert result is True

    @patch('git_integration.subprocess.run')
    def test_create_commit_git_error(self, mock_run, mock_git_failure):
        mock_run.side_effect = subprocess.CalledProcessError(1, ['git'], output='Error')
        with pytest.raises(Exception):
            git_integration.create_commit("fix: crash")
        mock_run.assert_called_once()


class TestCreateTag:
    @patch('git_integration.subprocess.run')
    def test_create_tag_success(self, mock_run, mock_git_success):
        mock_run.return_value = mock_git_success
        result = git_integration.create_tag("v1.0.0")
        mock_run.assert_called_once_with(
            ['git', 'tag', 'v1.0.0'],
            capture_output=True,
            check=False
        )
        assert result is True

    @patch('git_integration.subprocess.run')
    def test_create_tag_with_force(self, mock_run, mock_git_success):
        mock_run.return_value = mock_git_success
        result = git_integration.create_tag("v1.0.1", force=True)
        call_args = mock_run.call_args[0][0]
        assert '-f' in call_args
        assert result is True

    @patch('git_integration.subprocess.run')
    def test_create_tag_already_exists(self, mock_run, mock_git_failure):
        mock_run.return_value = MockCompletedProcess(returncode=1)
        with pytest.raises(Exception):
            git_integration.create_tag("v1.0.0")
        mock_run.assert_called_once()


class TestPushToRemote:
    @patch('git_integration.subprocess.run')
    def test_push_to_remote_success(self, mock_run, mock_git_success):
        mock_run.return_value = mock_git_success
        result = git_integration.push_to_remote(remote='origin', branch='main')
        mock_run.assert_called_once_with(
            ['git', 'push', 'origin', 'main'],
            capture_output=True,
            check=False
        )
        assert result is True

    @patch('git_integration.subprocess.run')
    def test_push_to_remote_force(self, mock_run, mock_git_success):
        mock_run.return_value = mock_git_success
        result = git_integration.push_to_remote(force=True)
        call_args = mock_run.call_args[0][0]
        assert '--force' in call_args
        assert result is True

    @patch('git_integration.subprocess.run')
    def test_push_to_remote_auth_failure(self, mock_run, mock_git_auth_failure):
        mock_run.return_value = MockCompletedProcess(returncode=1)
        with pytest.raises(Exception):
            git_integration.push_to_remote()
        mock_run.assert_called_once()


class TestIntegrationWorkflow:
    @patch('git_integration.subprocess.run')
    def test_full_workflow_mocked(self, mock_run):
        mock_run.return_value = MockCompletedProcess(returncode=0)
        
        git_integration.create_commit("v1.0.0")
        git_integration.create_tag("v1.0.0")
        git_integration.push_to_remote()
        
        assert mock_run.call_count == 3