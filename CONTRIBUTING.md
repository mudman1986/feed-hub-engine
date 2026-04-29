# Contributing to Feed Hub Engine

Thank you for your interest in contributing to Feed Hub Engine! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

Feed Hub Engine hosts the reusable RSS aggregation workflow, shared site generator, and demo deployment used to test feed hub changes before consumers adopt them.

### Repository Structure

- `.github/workflows/` - GitHub Actions workflow definitions
- `.github/scripts/` - Shell scripts used by workflows
- `site/` - GitHub Pages content (HTML, CSS, JavaScript)
- `tests/` - Playwright UI tests

## Development Setup

### Prerequisites

- **Node.js** (v18 or higher) - for JavaScript dependencies and testing
- **Python 3.x** - for workflow scripts
- **Bash** - for shell scripts
- **Git** - for version control

### Initial Setup

1. **Fork and clone the repository**:

   ```bash
   git clone https://github.com/YOUR_USERNAME/feed-hub-engine.git
   cd feed-hub-engine
   ```

2. **Install JavaScript dependencies**:

   ```bash
   npm install
   ```

3. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers** (for UI testing):

   ```bash
   npx playwright install
   ```

### Running Tests Locally

**IMPORTANT**: Always run tests before submitting a pull request.

1. **Generate test data** (required for UI tests):

   ```bash
   bash .github/scripts/generate-test-data.sh
   ```

2. **Run JavaScript unit tests**:

   ```bash
   npm test
   ```

3. **Run Python unit tests**:

   ```bash
   python3 -m pytest tests/python/rss-processing/ -v
   ```

4. **Run UI tests**:

   ```bash
   npm run test:ui
   ```

5. **Run shell script tests**:

   ```bash
   bats .github/scripts/test_*.bats
   ```

See [TESTING.md](TESTING.md) for detailed testing documentation.

### Running Linters Locally

This project uses Super-Linter for code quality. Run it locally before submitting:

```bash
docker run --rm \
  -e RUN_LOCAL=true \
  -e VALIDATE_ALL_CODEBASE=true \
  -e DEFAULT_BRANCH=main \
  -e IGNORE_GITIGNORED_FILES=true \
  -v $(pwd):/tmp/lint \
  ghcr.io/super-linter/super-linter:v8.3.2
```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bugfixes** - Fix issues in the codebase
- **New features** - Add functionality to the feed aggregator
- **Documentation** - Improve or add documentation
- **UI improvements** - Enhance the user interface
- **Feed additions** - Suggest new RSS feeds to track
- **Tests** - Add or improve test coverage

### Adding New RSS Feeds

To add a new RSS feed source:

1. Edit `config/rss-feeds.json`
2. Add your feed following the existing format:

   ```json
   {
     "name": "Feed Name",
     "url": "https://example.com/feed.xml",
     "category": "Category Name"
   }
   ```

3. Test the feed locally by running the collection action
4. Submit a pull request with your addition

## Coding Standards

### General Principles

- **Write clean, readable code** with meaningful variable names
- **Keep functions focused** - one function, one responsibility
- **Add comments** for complex logic
- **Follow existing patterns** in the codebase
- **Write tests** for new features and bugfixes

### Language-Specific Guidelines

#### JavaScript

- Use ES6+ syntax
- Use `const` and `let`, not `var`
- Write unit tests with Jest
- Follow existing code style

#### Python

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for functions and classes
- Use `feedparser` for RSS parsing
- Write pytest tests for new functionality

#### Shell Scripts

- Use `#!/usr/bin/env bash` shebang
- Set strict mode: `set -euo pipefail`
- Quote all variables: `"$VAR"` not `$VAR`
- Use tabs for indentation (shfmt requirement)
- Write BATS tests for new scripts

#### CSS/HTML

- Use semantic HTML elements
- Support both light and dark themes
- Ensure mobile responsiveness
- Follow accessibility best practices (ARIA labels, semantic markup)

## Testing Requirements

**All contributions must include tests.** This is mandatory for:

- Bugfixes: Add a test that reproduces the bug
- New features: Add tests for all new functionality
- UI changes: Add or update Playwright UI tests

### Test Execution Order

1. **UI Tests** (CRITICAL for site changes)
2. JavaScript unit tests
3. Python unit tests
4. Shell script tests

**For UI changes**, always:

1. Generate test data: `bash .github/scripts/generate-test-data.sh`
2. Run UI tests: `npm run test:ui`
3. Verify all tests pass
4. Test on multiple screen sizes

## Pull Request Process

### Before Submitting

1. ✅ **Run all tests** - ensure 100% pass rate
2. ✅ **Run super-linter** - fix all linting errors
3. ✅ **Update documentation** - if needed
4. ✅ **Add tests** - for new features or bugfixes
5. ✅ **Verify UI** - test on desktop, tablet, and mobile (for UI changes)

### Submitting a Pull Request

1. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with clear, focused commits

3. **Push to your fork**:

   ```bash
   git push origin feature/your-feature-name
   ```

4. **Open a Pull Request** with:
   - Clear title describing the change
   - Description of what changed and why
   - Reference to related issues (e.g., "Fixes #123")
   - Screenshots (for UI changes)

### PR Review Process

- All PRs require passing CI checks (tests, linting, security scans)
- Maintainers will review your code and may request changes
- Address feedback by pushing new commits to your branch
- Once approved, maintainers will merge your PR

### Commit Message Guidelines

Write clear, descriptive commit messages:

- Use present tense: "Add feature" not "Added feature"
- Be specific: "Fix theme toggle on mobile" not "Fix bug"
- Reference issues: "Fix theme toggle on mobile (fixes #123)"

## Issue Reporting

### Before Creating an Issue

- Search existing issues to avoid duplicates
- Verify the issue exists in the latest version

### Creating an Issue

Use the appropriate issue template:

- **Bug Report**: For reporting bugs
- **Feature Request**: For suggesting new features
- **Refactor**: For code improvement suggestions
- **UX Enhancement**: For user experience improvements

Include:

- **Clear title** - be specific
- **Description** - what happened vs. what you expected
- **Steps to reproduce** - for bugs
- **Screenshots** - if applicable
- **Environment** - browser, OS (if relevant)

## Getting Help

- **Questions?** Open a discussion or issue
- **Stuck?** Check the [TESTING.md](TESTING.md) and [README.md](README.md)
- **Need clarification?** Ask in your pull request or issue

## Recognition

Contributors are recognized in the project and their contributions are valued. Thank you for making Feed Hub Engine better!

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Feed Hub Engine! 🚀
