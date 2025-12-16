# Contributing to Agentic Analytics

Thank you for your interest in contributing to Agentic Analytics! This guide will help you get started.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/AgenticAnalytics.git
   cd AgenticAnalytics
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your environment:
   ```bash
   cp .env.example .env
   # Add your OPENAI_API_KEY to .env
   ```

## Development Workflow

### Making Changes

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards (see below)

3. Test your changes:
   ```bash
   python test_basic.py
   python examples/basic_usage.py
   streamlit run app.py
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Open a Pull Request

## Coding Standards

### Python Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Write docstrings for all functions and classes
- Keep functions focused and small

### Agent Development

When creating a new agent:

1. Inherit from `BaseAgent`:
   ```python
   from agentic_analytics.agents.base import BaseAgent
   
   class MyAgent(BaseAgent):
       def __init__(self):
           super().__init__(
               name="My Agent",
               description="What this agent does"
           )
   ```

2. Implement the `execute` method:
   ```python
   def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
       try:
           # Your logic here
           return {
               "success": True,
               "result": ...,
               "agent": self.name
           }
       except Exception as e:
           return {
               "success": False,
               "error": str(e),
               "agent": self.name
           }
   ```

3. Add to orchestrator workflow in `orchestrator.py`

### Documentation

- Update README.md if adding major features
- Add docstrings to all new functions
- Update API.md for new public APIs
- Include examples in `examples/` directory

### Testing

- Write unit tests for new functionality
- Ensure existing tests pass
- Test edge cases and error conditions
- Test without API key for graceful degradation

## Project Structure

```
AgenticAnalytics/
├── agentic_analytics/      # Main package
│   ├── agents/            # Agent implementations
│   ├── config/            # Configuration
│   ├── rag/               # RAG system
│   ├── utils/             # Utilities
│   └── orchestrator.py    # Main orchestrator
├── docs/                  # Documentation
├── examples/              # Example scripts
├── tests/                 # Tests
└── app.py                # Streamlit app
```

## Areas for Contribution

### High Priority

1. **Database Support**: Add PostgreSQL, MySQL support
2. **Testing**: Expand test coverage
3. **Error Handling**: Improve error messages and recovery
4. **Performance**: Optimize query execution

### Medium Priority

1. **Additional Agents**: Time series analysis, forecasting
2. **Visualizations**: More chart types, interactive features
3. **Export**: PDF reports, Excel exports
4. **Query History**: Save and replay queries

### Documentation

1. Video tutorials
2. More examples
3. Best practices guide
4. Troubleshooting guide

## Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: How to reproduce the bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: Python version, OS, package versions
6. **Logs**: Any error messages or logs

Use the issue template:

```markdown
**Bug Description**
A clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. Run command...
2. Enter input...
3. See error...

**Expected Behavior**
What should happen.

**Screenshots**
If applicable, add screenshots.

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.11]
- Package versions: [run `pip list`]
```

## Feature Requests

We welcome feature requests! Please include:

1. **Use Case**: What problem does this solve?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Any alternative approaches?
4. **Additional Context**: Any other relevant information

## Code Review Process

1. All PRs require review from maintainers
2. CI checks must pass
3. Code must follow style guidelines
4. Tests must pass
5. Documentation must be updated

## Questions?

- Open a GitHub issue with the `question` label
- Check existing documentation in `docs/`
- Review examples in `examples/`

## License

By contributing, you agree that your contributions will be licensed under the project's license.

## Code of Conduct

Be respectful and constructive in all interactions. We strive to maintain a welcoming community.

Thank you for contributing! 🎉
