# Contributing to Bid AI Agent

Thank you for your interest in contributing to Bid AI Agent! This document provides guidelines for contributing to the project.

## Code of Conduct

This project follows a security-first approach. All contributions must maintain the highest security standards.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/bid-ai-agent.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest tests/ -v`
6. Commit your changes: `git commit -m "feat: add amazing feature"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install black pylint mypy pytest pytest-cov

# Run tests
pytest tests/ -v --cov

# Run linters
black .
pylint **/*.py
mypy .
```

## Coding Standards

### Security Requirements

**CRITICAL:** This application handles sensitive business documents. Every contribution MUST:

1. Follow OWASP security guidelines
2. Never introduce dependencies with known vulnerabilities
3. Validate all inputs
4. Never log sensitive data
5. Maintain local-only processing (no external API calls)

### Code Style

- Follow PEP 8
- Use type hints for all function parameters and returns
- Write docstrings for all public functions and classes
- Maximum line length: 100 characters
- Use meaningful variable names

### Testing

- Write tests for all new features
- Maintain minimum 80% code coverage
- Include unit tests and integration tests
- Test edge cases and error conditions

## Commit Messages

Follow conventional commit format:

```
type(scope): subject

body

footer
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Example:
```
feat(classifier): add support for new document type

- Implemented CNDT (Certidão Negativa de Débitos Trabalhistas) recognition
- Added pattern matching for CNH documents
- Updated tests and documentation

Closes #123
```

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md (if applicable)
5. Request review from maintainers
6. Address review feedback
7. Wait for approval and merge

## Security Vulnerability Reporting

**DO NOT** create public issues for security vulnerabilities.

Instead, email security details to: [security contact - to be added]

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Questions?

Open a discussion in the GitHub Discussions tab or create an issue with the `question` label.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
