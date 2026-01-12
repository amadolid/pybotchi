# Contributing to PyBotchi

Thank you for your interest in contributing to PyBotchi! We welcome bug reports, feature requests, documentation improvements, code contributions, and example applications.

## 🚀 Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/pybotchi.git
   cd pybotchi
   ```

2. **Install dependencies**
   ```bash
   pip install poetry
   poetry install --all-extras
   ```

3. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

   Once installed, pre-commit will automatically run code formatting and quality checks on every commit.

4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🧪 Code Quality

Pre-commit hooks will automatically run formatting and quality checks when you commit. To manually run checks:

```bash
# Run all pre-commit hooks manually
pre-commit run --all-files

# Or run specific tools
ruff check --fix .
ruff format .
mypy pybotchi
```

## 📝 Code Style

- **Line length**: 120 characters max
- **Python**: 3.12+ target
- **Docstrings**: Single sentence if descriptive enough, Google-style for complex cases
- **Type hints**: Required for function signatures

Example:
```python
"""Example action module demonstrating PyBotchi coding standards."""

from pybotchi import Action, ActionReturn, Context
from pydantic import Field


class ExampleAction(Action):
    """Processes user requests and generates responses."""

    field_name: str = Field(description="Field description")

    async def pre(self, context: Context) -> ActionReturn:
        """Execute pre-processing logic before child actions."""
        return ActionReturn.GO
```

## 💬 Commit Messages

Use clear, descriptive commit messages with capitalized type prefixes:

```
[TYPE]: Description

[optional body]
```

**Types** (capitalize and use any descriptive term based on intent):
- `[MAJOR]` - Breaking changes, major refactors
- `[MINOR]` - New features, enhancements
- `[BUGFIX]` - Bug fixes
- `[DOCS]` - Documentation changes
- `[CHORE]` - Maintenance, dependencies
- `[PERF]` - Performance improvements
- Or any other descriptive type that clearly communicates the change

**Examples:**
```
[MINOR]: Add custom metadata support for gRPC connections
[BUGFIX]: Resolve SSE transport disconnection in MCP
[DOCS]: Update installation instructions
[MAJOR]: Refactor Action lifecycle hooks
[SECURITY]: Update authentication flow
[STYLE]: Improve code formatting consistency
```

## 🔄 Pull Request Process

1. **Commit your changes** - Pre-commit hooks will automatically check code quality

2. **Update documentation** if needed

3. **Rebase on main**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

4. **Push and create PR** with:
   - Clear title (following commit format)
   - Description of changes
   - Reference to related issues (e.g., "Fixes #123")

### PR Checklist
- [ ] Code follows style guidelines (enforced by pre-commit)
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

## 🐛 Reporting Bugs

Include in your bug report:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment (PyBotchi version, Python version, OS)
- Error messages/stack traces

## 💡 Feature Requests

Include in your proposal:
- Feature description
- Use case and problem it solves
- Proposed implementation (if you have ideas)

## 📖 Documentation

Help improve:
- API reference documentation
- Step-by-step tutorials and guides
- Real-world examples
- Best practices and patterns

## 🤝 Community Guidelines

- Be respectful and constructive
- Provide helpful feedback
- Work collaboratively
- Welcome contributors of all backgrounds

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to PyBotchi! 🚀
