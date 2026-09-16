# Python Test Examples (pytest)

Comprehensive pytest patterns including fixtures, mocking, and test structure.

---

## Test Structure

```python
import pytest
from module import function_under_test

class TestFunctionName:
    """Tests for function_name"""

    def test_normal_input(self):
        """Happy path: normal expected usage"""
        result = function_under_test("valid_input")
        assert result == expected_output

    def test_empty_input(self):
        """Edge case: empty input"""
        result = function_under_test("")
        assert result == default_value

    def test_boundary_value(self):
        """Edge case: boundary value"""
        result = function_under_test(MAX_VALUE)
        assert result == boundary_result

    def test_invalid_input_raises(self):
        """Error case: invalid input raises exception"""
        with pytest.raises(ValueError, match="expected message"):
            function_under_test(None)

    @pytest.fixture
    def mock_dependency(self, mocker):
        """Mock external dependency (the `mocker` fixture requires the pytest-mock plugin)"""
        return mocker.patch('module.external_service')

    def test_with_mocked_dependency(self, mock_dependency):
        """Integration: with mocked external service"""
        mock_dependency.return_value = {"data": "mocked"}
        result = function_under_test("input")
        assert result == expected_with_mock
```

## Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific file
pytest tests/test_module.py

# Specific test
pytest tests/test_module.py::test_function
```

## Coverage Analysis

```bash
# Count functions
grep -r "^def " src/ --include="*.py" | wc -l
grep -r "^def test_" tests/ --include="*.py" | wc -l

# Coverage report
pytest --cov=src --cov-report=term-missing
```

## Detect Project Type

```bash
test -f pytest.ini || test -f pyproject.toml
```
