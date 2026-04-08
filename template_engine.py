from __future__ import annotations
from typing import Dict, List, Any, Optional, TypedDict
from pathlib import Path
import datetime
import jinja2
import git


class ChangelogEntry(TypedDict):
    """Represents a single change entry in a changelog version."""
    title: str
    description: str
    type: str


class VersionEntry(TypedDict):
    """Represents a version block in the changelog."""
    version: str
    date: str
    changes: List[ChangelogEntry]


class ChangelogTemplateEngine:
    """
    Engine for formatting summarized changelog data into Markdown files using Jinja2 templates.
    Supports standard formats like Keep a Changelog and allows loading custom templates.
    """

    DEFAULT_KEEP_A_CHANGELOG_TEMPLATE: str = (
        "# Changelog\n\n"
        "All notable changes to this project will be documented in this file.\n\n"
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\n"
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
        "{% for entry in changelog_entries %}## [{{ entry.version }}] - {{ entry.date }}{% for change in entry.changes %}\n{% if change.type == 'Added' %}### Added{% elif change.type == 'Changed' %}### Changed{% elif change.type == 'Deprecated' %}### Deprecated{% elif change.type == 'Removed' %}### Removed{% elif change.type == 'Fixed' %}### Fixed{% elif change.type == 'Security' %}### Security{% endif %}\n- {{ change.title }}{% if change.description %}\n  {{ change.description }}{% endif %}{% endfor %}{% endfor %}"
    )

    def __init__(self, templates_dir: Optional[Path] = None) -> None:
        """
        Initialize the template engine.

        Args:
            templates_dir: Optional path to a directory containing custom Jinja2 templates.
        """
        self._templates_dir: Optional[Path] = templates_dir
        self._jinja_loader: Optional[jinja2.FileSystemLoader] = None
        self._env: jinja2.Environment = jinja2.Environment(
            loader=jinja2.ChoiceLoader([
                jinja2.DictLoader({'default.md': self.DEFAULT_KEEP_A_CHANGELOG_TEMPLATE}),
            ])
        )
        self._setup_environment()

    def _setup_environment(self) -> None:
        """Configure the Jinja2 environment with filters and load external templates."""
        try:
            if self._templates_dir and self._templates_dir.exists():
                self._jinja_loader = jinja2.FileSystemLoader(self._templates_dir)
                self._env.loader = jinja2.ChoiceLoader([
                    self._jinja_loader,
                    jinja2.ChoiceLoader([
                        jinja2.DictLoader({'default.md': self.DEFAULT_KEEP_A_CHANGELOG_TEMPLATE})
                    ])
                ])
        except jinja2.TemplateError as e:
            raise TemplateLoadingError(f"Failed to configure Jinja2 environment: {e}")
        except OSError as e:
            raise TemplateLoadingError(f"Failed to access template directory: {e}")

    def get_template(self, name: str = 'default') -> jinja2.Template:
        """
        Retrieve a template by name from the environment.

        Args:
            name: The name of the template to load.

        Returns:
            A compiled Jinja2 template.

        Raises:
            TemplateLoadingError: If the template cannot be loaded.
        """
        try:
            template = self._env.get_template(name)
            return template
        except jinja2.TemplateNotFound:
            raise TemplateLoadingError(f"Template '{name}' not found in available templates.")

    def render_changelog(self, data: Dict[str, Any], template_name: str = 'default') -> str:
        """
        Render a changelog string from structured data using the specified template.

        Args:
            data: Dictionary containing 'changelog_entries' key with list of VersionEntry dicts.
            template_name: Name of the Jinja2 template to use.

        Returns:
            The rendered Markdown string.

        Raises:
            TemplateRenderingError: If data validation fails or rendering fails.
        """
        try:
            if 'changelog_entries' not in data:
                raise TemplateRenderingError("Data dictionary must contain 'changelog_entries'.")
            
            entries: List[VersionEntry] = data['changelog_entries']
            
            self._validate_data_structure(entries)
            
            template = self.get_template(template_name)
            rendered_content: str = template.render(changelog_entries=entries)
            
            return rendered_content

        except TemplateLoadingError as e:
            raise