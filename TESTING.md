# Testing Documentation

## Overview

This baseball-stats project now has comprehensive unit test coverage using pytest. The test suite validates core functionality across utilities, analysis modules, and data management.

## Test Statistics

- **Total Tests**: 180+
- **Test Coverage**: ~35% and growing
- **Test Frameworks**: pytest, pytest-cov, pytest-mock

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run with Coverage Report
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### Run Specific Test File
```bash
pytest tests/test_utils_helpers.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_analysis_metrics.py::TestWOBA -v
```

### Run with HTML Coverage Report
```bash
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Organization

```
tests/
├── __init__.py
├── conftest.py                          # Shared fixtures
├── test_utils_helpers.py                # Helper function tests (60+ tests)
├── test_analysis_metrics.py             # Metrics calculation tests (40+ tests)
├── test_analysis_free_agent.py          # Free agent analyzer tests (30+ tests)
├── test_analysis_aging_curves.py        # Aging curves tests (25+ tests)
├── test_analysis_breakout_detector.py   # Breakout detector tests (25+ tests)
└── test_data_contract.py                # Contract data tests (20+ tests)
```

## Test Fixtures

Common fixtures are available in `tests/conftest.py`:

- `sample_statcast_data`: 100 rows of simulated Statcast pitch data
- `sample_batting_data`: 5 elite MLB batters with stats
- `sample_pitching_data`: 5 elite MLB pitchers with stats
- `sample_free_agents`: Sample 2025 free agent data
- `sample_player_names`: List of player names for testing
- `mock_statcast_response`: Mock response from pybaseball

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
Tests for individual functions and methods in isolation.

### Integration Tests (`@pytest.mark.integration`)
Tests that verify multiple components work together.

### Data Tests (`@pytest.mark.data`)
Tests that may require external data sources (usually mocked).

### Slow Tests (`@pytest.mark.slow`)
Tests that take significant time to run.

## Running Specific Test Categories

```bash
# Run only unit tests
pytest tests/ -m unit

# Run all except slow tests
pytest tests/ -m "not slow"

# Run integration and data tests
pytest tests/ -m "integration or data"
```

## Coverage Goals

### Current Coverage by Module

| Module | Coverage | Tests |
|--------|----------|-------|
| src/utils/helpers.py | 90% | 60+ |
| src/analysis/metrics.py | 100% | 40+ |
| src/analysis/free_agent_analyzer.py | 76% | 30+ |
| src/analysis/aging_curves.py | 69% | 25+ |
| src/analysis/breakout_detector.py | 79% | 25+ |
| src/data/contract_data.py | 100% | 20+ |

### Coverage Targets

- **Critical modules** (metrics, helpers): 90%+
- **Analysis modules**: 75%+
- **Data fetchers**: 60%+ (limited by external dependencies)
- **Models**: 50%+ (complex statistical models)

## Writing New Tests

### Test Structure

```python
import pytest
import pandas as pd
from src.analysis.metrics import calculate_woba

class TestWOBA:
    """Tests for wOBA calculation."""

    def test_calculate_woba_basic(self):
        """Test basic wOBA calculation."""
        df = pd.DataFrame({
            'events': ['single', 'walk', 'home_run']
        })
        result = calculate_woba(df)

        assert isinstance(result, pd.Series)
        assert len(result) == 3

    def test_calculate_woba_with_nulls(self):
        """Test wOBA with null events."""
        df = pd.DataFrame({
            'events': ['single', None, 'home_run']
        })
        result = calculate_woba(df)

        assert result.iloc[1] == 0.0  # null treated as 0
```

### Best Practices

1. **One concept per test**: Each test should verify one specific behavior
2. **Descriptive names**: Use clear, descriptive test names
3. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification
4. **Use fixtures**: Leverage shared fixtures from conftest.py
5. **Test edge cases**: Include tests for empty data, nulls, invalid inputs
6. **Mock external calls**: Use pytest-mock for external API calls

### Example: Testing Error Handling

```python
def test_invalid_date_format(self):
    """Test that invalid date format raises ValueError."""
    fetcher = StatcastFetcher()

    with pytest.raises(ValueError, match="Invalid date format"):
        fetcher.get_statcast_data("bad-date", "2024-01-01")
```

## Continuous Integration

Tests run automatically on:
- Every push to main/develop branches
- Every pull request
- Multiple Python versions (3.9, 3.10, 3.11)

See `.github/workflows/tests.yml` for CI configuration.

## Known Issues

### Floating Point Precision

Some tests may fail due to floating point precision. Use approximate comparisons:

```python
# Instead of:
assert result == 0.020

# Use:
assert abs(result - 0.020) < 0.001
```

### External Dependencies

Tests for data fetchers (pybaseball) are integration tests and may:
- Require network connection
- Be slower
- Occasionally fail due to API issues

## Debugging Failed Tests

### Verbose Output
```bash
pytest tests/ -v --tb=long
```

### Stop at First Failure
```bash
pytest tests/ -x
```

### Run Last Failed Tests
```bash
pytest tests/ --lf
```

### Debug with PDB
```bash
pytest tests/ --pdb
```

## Test Maintenance

### Regular Tasks

1. **Update fixtures**: Keep sample data current with real MLB seasons
2. **Add tests for new features**: Maintain 75%+ coverage for new code
3. **Review slow tests**: Optimize or mark appropriately
4. **Clean up skipped tests**: Address TODOs and skipped tests

### Adding Tests for New Features

When adding a new module:

1. Create corresponding test file: `tests/test_<module_name>.py`
2. Add fixtures if needed in conftest.py
3. Aim for 75%+ coverage
4. Include error handling tests
5. Test edge cases (empty data, nulls, invalid inputs)

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [pytest-mock](https://pytest-mock.readthedocs.io/)

## Contributing

When submitting a PR:

1. Ensure all tests pass locally
2. Add tests for new functionality
3. Maintain or improve coverage
4. Update this documentation if needed

```bash
# Before submitting PR
pytest tests/ --cov=src --cov-report=term-missing
```

## Questions?

For questions about testing:
- Check existing tests for examples
- Review pytest documentation
- Open an issue for clarification
