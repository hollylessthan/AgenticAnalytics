# Contributing to Agentic Analytics

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/AgenticAnalytics.git`
3. Create a virtual environment: `python -m venv venv`
4. Install dependencies: `pip install -r requirements.txt`
5. Install dev dependencies: `pip install pytest pytest-cov black flake8`

## Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `pytest tests/`
4. Format code: `black src/ tests/`
5. Lint code: `flake8 src/ tests/`
6. Commit changes: `git commit -m "Description of changes"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Code Style

- Follow PEP 8 style guide
- Use Black for formatting (line length: 100)
- Add docstrings to all functions and classes
- Use type hints where appropriate

Example:
```python
def process_data(data: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """Process the input data.
    
    Args:
        data: Input DataFrame
        threshold: Processing threshold
        
    Returns:
        Processed DataFrame
    """
    # Implementation
    return processed_data
```

## Testing

- Write unit tests for all new features
- Maintain test coverage above 80%
- Use pytest for testing
- Mock external dependencies (OpenAI API, databases)

Run tests:
```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/test_agents.py
```

## Adding New Agents

1. Create agent file in `src/agents/`
2. Inherit from `BaseAgent`
3. Implement `execute()` method
4. Add to orchestrator workflow
5. Write tests
6. Update documentation

Example:
```python
from agents.base import BaseAgent, AgentState

class NewAgent(BaseAgent):
    """Your new agent."""
    
    def __init__(self, llm):
        super().__init__("new_agent", "Agent description")
        self.llm = llm
    
    def execute(self, state: AgentState) -> AgentState:
        """Execute agent logic."""
        # Your implementation
        return state
```

## Adding Vector Store Implementations

1. Create implementation in `src/rag/vector_store.py`
2. Inherit from `VectorStoreBase`
3. Implement required methods
4. Add to factory function
5. Update configuration
6. Write tests

## Documentation

- Update README.md for major features
- Add docstrings to all public functions/classes
- Include usage examples in `examples/`
- Update type hints and comments

## Pull Request Guidelines

- Provide clear description of changes
- Reference related issues
- Include test results
- Update documentation
- Follow commit message conventions:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation
  - `test:` for tests
  - `refactor:` for refactoring
  - `chore:` for maintenance

## Questions?

Open an issue for:
- Bug reports
- Feature requests
- Questions about implementation
- General discussion

Thank you for contributing! 🎉
