![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![GitHub Stars](https://img.shields.io/github/stars/dsoles-eth/dev-changelog-ai?style=social)

# Changelog AI Generator

[**pypi**](https://pypi.org/project/dev-changelog-ai/) | [**Documentation**](#usage)

**Changelog AI Generator** is an intelligent command-line tool designed to automate the maintenance of project documentation. It analyzes your Git commit history, leverages Large Language Models (LLMs) to interpret commit messages, and generates polished, semantic `CHANGELOG.md` files that meet industry standards.

Built for open source maintainers and DevOps engineers, this tool eliminates the manual overhead of documenting releases, ensuring your project remains transparent and professional without the friction of writing release notes by hand.

## Features

- 🚀 **Semantic Analysis**: Automatically classifies commits into standard sections (Added, Changed, Deprecated, Removed, Fixed).
- 🤖 **LLM-Powered Summarization**: Groups raw commit messages into meaningful high-level summaries using OpenAI integration.
- 🛡️ **Semantic Versioning**: Validates generated output against Semantic Versioning (SemVer) standards.
- 🎨 **Customizable Templates**: Uses Jinja2 to render changelogs in various formats to match your project's style.
- 🔗 **Git Workflow Integration**: Handles commit creation and tagging workflows directly from the generator.
- 🔒 **Privacy First**: Designed to run locally; API keys are handled securely via environment variables.

## Installation

Install the package via PyPI:

```bash
pip install dev-changelog-ai
```

Alternatively, install from source:

```bash
git clone https://github.com/dsoles-eth/dev-changelog-ai
cd dev-changelog-ai
pip install -e .
```

## Quick Start

After installing, configure your API key and generate a changelog for your current repository.

1. **Set your API Key:**

```bash
export OPENAI_API_KEY="your-api-key"
```

2. **Generate the Changelog:**

Run the following command to analyze the last 50 commits and create a changelog for version `v1.1.0`:

```bash
dev-changelog-ai generate --version v1.1.0 --output CHANGELOG.md --limit 50
```

3. **Review and Push:**

The tool will output a summary of the changes and save them to `CHANGELOG.md`. Review the file and commit the changes manually to your repository.

## Usage

### Generate Release Notes

Use the `generate` subcommand to create the changelog file.

```bash
# Basic usage
dev-changelog-ai generate --version 1.0.0

# Specify a commit range (e.g., from last tag)
dev-changelog-ai generate --from-tag v0.9.0 --to HEAD

# Use a specific template file
dev-changelog-ai generate --template custom.j2
```

### Configuration

You can define default settings in a `.changelog-ai` configuration file in your project root:

```json
{
  "model": "gpt-3.5-turbo",
  "template": "standard",
  "include_metadata": true,
  "commit_prefixes": ["feat", "fix", "docs", "style", "refactor"]
}
```

### Push to Remote

If you have write access to the repository, you can commit and tag the generated changelog automatically using the `git_integration` module:

```bash
dev-changelog-ai generate --version v1.1.0 --commit --tag --push
```

## Architecture

The project is modular, allowing for flexibility and testing. Key components include:

- **`commit_parser`**: Parses Git history using `GitPython` to extract metadata, commit types, and descriptions.
- **`ai_summarizer`**: Interfaces with OpenAI to group and summarize raw commits into human-readable summaries.
- **`template_engine`**: Renders the summarized data into `CHANGELOG.md` structures using `Jinja2` templates.
- **`validator`**: Validates generated content against semantic versioning rules and format standards before output.
- **`git_integration`**: Manages commit creation, lightweight tagging, and push operations to remote repositories.

## Contributing

We welcome contributions! Whether you want to improve the AI summarization logic, add new template styles, or fix bugs, please follow these steps:

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  Make your changes and ensure tests pass.
4.  Commit