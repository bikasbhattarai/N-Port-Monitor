# Contributing to N-Port Monitor

First off, thank you for considering contributing to N-Port Monitor! It's people like you that make this project better.

## Code of Conduct

By participating in this project, you are expected to uphold our code of conduct: be respectful, inclusive, and constructive in all interactions.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Describe the behavior you observed and what you expected**
- **Include screenshots if applicable**
- **Include your environment details** (OS, Python version, browser)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description of the proposed enhancement**
- **Explain why this enhancement would be useful**
- **List any alternatives you've considered**

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Make your changes** following the coding standards below
4. **Add tests** if applicable
5. **Run the test suite**: `pytest tests/ -v`
6. **Run the linter**: `flake8 data_monitor/`
7. **Commit your changes** with a clear commit message
8. **Push to your fork** and submit a pull request

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and small
- Use type hints where appropriate

### Example:

```python
def get_sensor_status(sensor_id: int) -> Optional[str]:
    """
    Retrieve the current status of a sensor.
    
    Args:
        sensor_id: The unique identifier of the sensor.
        
    Returns:
        The sensor status ('green', 'red', 'unknown') or None if not found.
    """
    # Implementation here
    pass
```

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests when relevant

### Example:

```
Add sensor history export feature

- Implement CSV export for sensor history data
- Add export button to station detail page
- Include timestamp formatting options

Fixes #123
```

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/N-Port-Monitor.git
   cd N-Port-Monitor
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

5. Run the development server:
   ```bash
   python run.py
   ```

## Project Structure

```
N-Port-Monitor/
├── data_monitor/          # Main application package
│   ├── app.py            # Flask routes and views
│   ├── config.py         # Configuration settings
│   ├── database.py       # Database operations
│   ├── monitor.py        # Sensor monitoring logic
│   ├── static/           # CSS, JS, images
│   └── templates/        # HTML templates
├── tests/                # Test files
├── docs/                 # Documentation
└── run.py               # Application entry point
```

## Testing

Run the full test suite:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=data_monitor --cov-report=html
```

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

Thank you for contributing! 🎉
