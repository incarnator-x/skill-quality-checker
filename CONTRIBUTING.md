# Contributing to Skill Quality Checker

Thank you for your interest in contributing! 🎉

## How to Contribute

### Reporting Issues
- Check existing issues first
- Provide clear reproduction steps
- Include tool version and environment details

### Suggesting Features
- Open an issue with "Feature Request" label
- Explain the use case
- Provide examples if possible

### Code Contributions

1. **Fork the repository**

2. **Create a feature branch**
```bash
git checkout -b feature/amazing-feature
```

3. **Make your changes**
- Follow PEP 8 style guide
- Add docstrings to functions
- Keep functions focused and small

4. **Test your changes**
```bash
# Test on a sample skill
python skill_quality_checker.py /path/to/test/skill/ --skip-ai
```

5. **Commit with clear messages**
```bash
git commit -m "Add: Support for Ruby code validation"
```

6. **Push and create Pull Request**
```bash
git push origin feature/amazing-feature
```

## Development Setup

```bash
# Clone your fork
git clone https://github.com/incarnator-x/skill-quality-checker.git
cd skill-quality-checker

# Install dependencies
pip install -r requirements.txt

# Make changes...

# Test
python skill_quality_checker.py examples/test_skill/ --skip-ai
```

## Code Style

- Use type hints where possible
- Write descriptive variable names
- Add comments for complex logic
- Keep functions under 50 lines when possible

## Adding New Validators

To add a new validator (e.g., image validator):

1. Create `validators/image_validator.py`
2. Implement the validation logic
3. Add to `skill_quality_checker.py` in `run_all_checks()`
4. Update `report_generator.py` to include results
5. Add tests

Example structure:

```python
# validators/image_validator.py
def validate_skill_images(skill_path: str) -> Dict:
    """
    Validate images in skill

    Args:
        skill_path: Path to skill directory

    Returns:
        Validation results dictionary
    """
    # Implementation
    pass
```

## Questions?

Open an issue or reach out!

Thank you for contributing! 🙏
