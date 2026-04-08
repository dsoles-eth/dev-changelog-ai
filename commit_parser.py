import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Iterator
from datetime import datetime
from pathlib import Path
import git

logger = logging.getLogger(__name__)


class CommitParseError(Exception):
    """Exception raised when a commit message cannot be parsed."""
    pass


class RepositoryError(Exception):
    """Exception raised when repository operations fail."""
    pass


@dataclass
class ParsedCommit:
    """Represents a parsed git commit with extracted metadata.

    Attributes:
        sha: The full commit hash (40 characters).
        author: Name and email of the commit author.
        date: Timestamp of when the commit was created.
        type: The conventional commit type (e.g., feat, fix).
        scope: Optional scope of the commit.
        description: The subject line of the commit.
        breaking_change: Boolean indicating if the commit contains a breaking change.
        body: Optional additional context in the commit message body.
    """
    sha: str
    author: str
    date: datetime
    type: str
    scope: Optional[str] = None
    description: str = ""
    breaking_change: bool = False
    body: Optional[str] = None


COMMIT_TYPES = {
    "feat", "fix", "docs", "style", "refactor",
    "perf", "test", "build", "ci", "chore", "revert"
}

COMMIT_REGEX = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(!)?"
    r"(?:\((?P<scope>[a-zA-Z0-9\-_.]+)\))?"
    r":\s(?P<description>.+)"
)


class CommitHistoryParser:
    """Parses git commit history to extract structured metadata.

    This class interfaces with a git repository to traverse commit history,
    extract metadata using conventional commit standards, and return
    structured ParsedCommit objects.
    """

    def __init__(self, repo_path: str) -> None:
        """Initialize the CommitHistoryParser with a repository path.

        Args:
            repo_path: The absolute or relative path to the git repository root.

        Raises:
            RepositoryError: If the provided path is not a valid git repository.
        """
        self.repo_path = Path(repo_path).resolve()
        
        try:
            self._repo = git.Repo(self.repo_path)
            logger.info(f"Initialized parser for repository at {self.repo_path}")
        except git.InvalidGitRepositoryError as e:
            raise RepositoryError(f"Invalid git repository path: {self.repo_path}") from e
        except git.NoSuchPathError as e:
            raise RepositoryError(f"Path does not exist: {self.repo_path}") from e

    def get_commits(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        max_count: Optional[int] = None,
    ) -> List[ParsedCommit]:
        """Retrieve and parse commits within a specified time range.

        Args:
            since: Retrieve commits created after this datetime. Defaults to repo root.
            until: Retrieve commits created before this datetime. Defaults to HEAD.
            max_count: Limit the number of commits returned. Defaults to None (all).

        Returns:
            A list of ParsedCommit objects containing metadata.

        Raises:
            RepositoryError: If the repository cannot be accessed during iteration.
            ValueError: If `until` is chronologically earlier than `since`.
        """
        if since and until and since > until:
            raise ValueError("Since date cannot be after until date.")

        try:
            commits = []
            iterator = self._repo.iter_commits(max_count=max_count)

            for commit in iterator:
                if until and commit.committed_datetime > until:
                    continue
                
                parsed = self._parse_single_commit(commit)
                if parsed:
                    if since and parsed.date < since:
                        break
                    commits.append(parsed)
            
            logger.info(f"Parsed {len(commits)} commits from repository {self.repo_path}")
            return commits

        except git.GitCommandError as e:
            raise RepositoryError(f"Git command failed during commit iteration") from e
        except Exception as e:
            raise RepositoryError(f"Unexpected error during repository access: {e}") from e

    def _parse_single_commit(self, commit: git.Commit) -> ParsedCommit:
        """Parse a single git.Commit object into a ParsedCommit dataclass.

        Args:
            commit: A git.Commit object from gitpython.

        Returns:
            A ParsedCommit object.

        Raises:
            CommitParseError: If the commit message format is unrecognizable.
        """
        try:
            message = commit.message
            # Strip trailing newline often present in gitpython messages
            message = message.rstrip() 
            
            if not message:
                raise CommitParseError("Commit message is empty.")

            subject, body, type_, scope, description, breaking_change = self._parse_message(message)
            
            # Fallback for non-conventional commits to ensure we still capture data
            if not type_:
                type_ = "chore"
                description = subject
            
            return ParsedCommit(
                sha=commit.hexsha,
                author=f"{commit.author.name} <{commit.author.email}>",
                date=commit.committed_datetime,
                type=type_,
                scope=scope,
                description=description,
                breaking_change=breaking_change,
                body=body if body else None
            )

        except Exception as e:
            logger.error(f"Failed to parse commit {commit.hexsha[:7]}: {e}")
            raise CommitParseError(f"Failed to parse commit message: {message[:50]}") from e

    def _parse_message(self, message: str) -> Tuple[str, Optional[str], Optional[str], Optional[str], str, bool]:
        """Parse a raw commit message string into components.

        Args:
            message: The raw string content of a commit message.

        Returns:
            A tuple containing (subject, body, type, scope, description, breaking_change).
        """
        try:
            # Separate subject and body (conventionally separated by double newline)
            parts = message.split("\n\n", 1)
            subject = parts[0]
            body = parts[1] if len(parts) > 1 else None

            match = COMMIT_REGEX.match(subject)
            if not match:
                return (subject, body, None, None, subject, False)

            data = match.groupdict()
            type_ = data["type"]
            scope = data["scope"]
            description = data["description"]
            # Check for breaking change marker in subject
            is_breaking = "!" in subject
            # If it's a breaking change, the ! is after type and before scope. 
            # The regex captures type but not the ! in the group.
            
            return (
                data["type"],
                body,
                type_,
                scope,
                description,
                is_breaking
            )
        except IndexError:
            logger.warning("Malformed commit subject line encountered.")
            return ("chore", None, "chore", None, message, False)
        except Exception as e:
            raise CommitParseError(f"Regex parsing failed for subject: {subject}") from e

    def get_repo_status(self) -> dict:
        """Get basic status information about the repository.

        Returns:
            A dictionary containing branch, head, and number of commits.
        """
        try:
            return {
                "branch": self._repo.active_branch.name if self._repo.head.is_detached else "HEAD-detached",
                "head_sha": self._repo.head.commit.hexsha[:7],
                "commit_count": len(list(self._repo.iter_commits()))
            }
        except AttributeError:
            return {"branch": "unknown", "head_sha": "unknown", "commit_count": 0}
        except Exception as e:
            logger.error(f"Error retrieving repo status: {e}")
            return {"branch": "unknown", "head_sha": "unknown", "commit_count": 0}