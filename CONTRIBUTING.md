# Contributing to Invoice MCP Server

Thank you for your interest in contributing to the Invoice MCP Server! This document provides guidelines and instructions for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Git

### Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/morenoraf/MCP_Server.git
cd MCP_Server

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install development dependencies
pip install -e ".[dev]"

# 4. Run tests to verify setup
pytest
```

## 📋 Development Workflow

### Branch Naming Convention

We use the following branch naming pattern for parallel development:

| Branch Type | Pattern | Example |
|------------|---------|---------|
| Features | `agent{N}/feature-name` | `agent1/new-api` |
| Bug Fixes | `agent{N}/fix-description` | `agent2/fix-security` |
| Documentation | `agent{N}/docs-topic` | `agent3/update-readme` |

### Using Git Worktrees for Parallel Development

This project supports parallel AI agent development using Git worktrees:

```bash
# Create worktrees for parallel work
git worktree add ../project-feature -b agent1/new-feature
git worktree add ../project-bugfix -b agent2/fix-bug
git worktree add ../project-docs -b agent3/update-docs

# List all worktrees
git worktree list

# Remove a worktree when done
git worktree remove ../project-feature
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/invoice_mcp_server --cov-report=term-missing

# Run specific test file
pytest tests/test_models.py -v
```

### Code Quality

```bash
# Type checking
mypy src/invoice_mcp_server

# Linting
ruff check src/invoice_mcp_server

# Format code
ruff format src/invoice_mcp_server
```

## 📝 Commit Message Guidelines

We follow conventional commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(api): Add health check endpoint for monitoring
fix(security): Prevent SQL injection in customer queries
docs(readme): Update installation instructions
```

## 🔀 Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Ensure all tests pass
4. Update documentation if needed
5. Submit a PR with a clear description

## 📚 MCP Protocol Guidelines

When adding new MCP primitives:

### Tools (Write Operations)
- Use for operations that modify state
- Return clear success/error responses
- Include input validation

### Resources (Read Operations)
- Use for data retrieval
- Support URI-based access pattern
- Return structured JSON data

### Prompts (Model Guidance)
- Provide clear instructions for AI models
- Include examples when helpful
- Keep prompts focused and specific

## 📞 Contact

For questions or support, please open an issue on GitHub.

---

*This document was generated with assistance from AI Agent 3 (Documentation)*
