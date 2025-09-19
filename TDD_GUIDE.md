# Test-Driven Development Guide for RogueSignalProtocol

This guide establishes the TDD workflow and best practices for the RogueSignalProtocol project.

## 🚀 Quick Start

### Run Tests
```bash
# Quick unit tests
python test_commands.py quick

# Full test suite with coverage
python test_commands.py full

# Run tests for changed files only
python test_commands.py changed

# Watch for file changes and auto-run tests
python test_commands.py watch
```

### Test Categories
We use pytest markers to categorize tests:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests across components  
- `@pytest.mark.performance` - Performance benchmarks
- `@pytest.mark.property` - Property-based tests
- `@pytest.mark.slow` - Tests that take >1 second
- `@pytest.mark.regression` - Regression tests for bug fixes

## 📋 TDD Workflow

### 1. Red Phase - Write Failing Test

```python
# tests/unit/test_new_feature.py
import pytest
from tests.fixtures.test_builders import player, enemy

def test_new_combat_mechanic():
    """Test the new combat mechanic."""
    test_player = player().with_cpu(100).build()
    test_enemy = enemy().hostile().build()
    
    # This should fail initially
    result = combat_system.apply_new_mechanic(test_player, test_enemy)
    
    assert result.success is True
    assert result.damage > 0
```

### 2. Green Phase - Make Test Pass

```python
# game_combat.py
def apply_new_mechanic(player, enemy):
    # Minimal implementation to make test pass
    return CombatResult(success=True, damage=10)
```

### 3. Refactor Phase - Improve Code

```python
# game_combat.py
def apply_new_mechanic(player, enemy):
    # Refactored implementation
    base_damage = calculate_base_damage(player, enemy)
    success_rate = calculate_success_rate(player, enemy)
    
    if random.random() < success_rate:
        return CombatResult(success=True, damage=base_damage)
    else:
        return CombatResult(success=False, damage=0)
```

## 🛠️ Test Infrastructure

### Test Builders
Use the builder pattern for creating test objects:

```python
from tests.fixtures.test_builders import player, enemy, scenario

# Fluent interface for test data
test_player = (player()
    .with_cpu(75)
    .with_heat(30) 
    .at_position(10, 10)
    .with_effect("stealth", 5)
    .build())

# Pre-built scenarios
combat_scenario = scenario().player_vs_single_enemy().build()
stealth_scenario = scenario().stealth_mission().build()
```

### Test Data Management
Use the test data manager for consistent data:

```python
from tests.fixtures.test_data import get_test_data, generate_save_data

# Get sample data
test_data = get_test_data()
sample_enemies = test_data.enemies

# Generate test save files
save_data = generate_save_data(level=3, cpu=50)
temp_save = create_temp_save(save_data)
```

### Property-Based Testing
Use Hypothesis for property-based tests:

```python
from hypothesis import given, strategies as st
from tests.property.test_position_properties import positions

@given(positions, positions)
def test_distance_symmetric(pos1, pos2):
    """Distance should be symmetric: d(A,B) = d(B,A)."""
    dist1 = calculate_manhattan_distance(pos1, pos2)
    dist2 = calculate_manhattan_distance(pos2, pos1)
    assert dist1 == dist2
```

## 📊 Test Quality Assurance

### Coverage Requirements
- **Minimum**: 70% overall coverage
- **Target**: 85% for core game logic
- **Critical**: 95% for combat and save systems

### Mutation Testing
```bash
# Run mutation tests to verify test quality
python mutmut_config.py run

# Check mutation score
python mutmut_config.py check
```

### Performance Benchmarks
```bash
# Run performance tests
python test_commands.py performance

# View benchmark history
pytest tests/performance/ --benchmark-compare
```

## 🔄 Continuous Integration

### GitHub Actions Pipeline
Our CI pipeline runs:

1. **Unit Tests** - All platforms and Python versions
2. **Integration Tests** - End-to-end functionality
3. **Property Tests** - Hypothesis-generated test cases
4. **Performance Tests** - Benchmark regressions
5. **Mutation Tests** - Test quality verification
6. **Code Quality** - Linting, formatting, type checking
7. **Security Scans** - Vulnerability detection

### Pre-commit Hooks
Install pre-commit hooks for automatic quality checks:

```bash
pip install pre-commit
pre-commit install
```

## 📁 Test Organization

```
tests/
├── unit/                 # Unit tests by module
│   ├── test_entities.py
│   ├── test_combat.py
│   └── ...
├── integration/          # Integration tests
│   └── test_game_flow.py
├── property/            # Property-based tests
│   └── test_position_properties.py
├── performance/         # Benchmark tests
│   └── test_benchmarks.py
├── fixtures/           # Test utilities
│   ├── test_builders.py
│   ├── test_data.py
│   └── mock_factories.py
└── conftest.py         # Shared fixtures
```

## 🎯 Best Practices

### Writing Tests

1. **Test Names**: Use descriptive names that explain the scenario
   ```python
   def test_player_dies_when_cpu_reaches_zero()
   def test_enemy_becomes_hostile_when_player_detected()
   ```

2. **AAA Pattern**: Arrange, Act, Assert
   ```python
   def test_heat_reduction_with_cooling_node():
       # Arrange
       player = player().with_heat(50).build()
       
       # Act
       process_heat_reduction(player, near_cooling_node=True)
       
       # Assert
       assert player.heat < 50
   ```

3. **Test Isolation**: Each test should be independent
   ```python
   def setup_method(self):
       """Reset state before each test."""
       self.player = player().build()
       self.game_state = game_state().build()
   ```

### Test Data

1. **Use Builders**: Prefer builders over direct object creation
2. **Meaningful Defaults**: Builders should have sensible defaults
3. **Fluent Interface**: Chain method calls for readability
4. **Test Scenarios**: Create pre-built scenarios for common cases

### Performance

1. **Mark Slow Tests**: Use `@pytest.mark.slow` for tests >1 second
2. **Benchmark Critical Paths**: Profile performance-sensitive code
3. **Set Thresholds**: Fail tests if performance degrades significantly

### Coverage

1. **Focus on Logic**: Prioritize testing business logic over getters/setters
2. **Edge Cases**: Test boundary conditions and error cases
3. **Integration Points**: Test module interactions
4. **Regression Tests**: Add tests for every bug fix

## 🚨 Troubleshooting

### Common Issues

1. **Flaky Tests**: Use `@pytest.mark.flaky` and fix non-deterministic behavior
2. **Slow Tests**: Profile and optimize or mark as slow
3. **Missing Coverage**: Use coverage reports to find untested code
4. **Test Pollution**: Ensure proper test isolation and cleanup

### Debug Commands

```bash
# Run specific test with detailed output
pytest tests/unit/test_combat.py::test_specific_function -v -s

# Debug test failures
pytest --pdb tests/unit/test_combat.py

# Profile test performance
pytest --profile tests/unit/test_combat.py

# Generate coverage report
pytest --cov=. --cov-report=html tests/
```

## 📈 Metrics & Monitoring

### Quality Metrics
- Test coverage percentage
- Mutation testing score  
- Performance benchmark trends
- Test execution time
- Code complexity metrics

### CI/CD Dashboards
- GitHub Actions build status
- Coverage trends over time
- Performance regression alerts
- Security vulnerability reports

---

## 🤝 Contributing

When contributing to the project:

1. **Write Tests First**: Follow TDD principles
2. **Maintain Coverage**: Don't decrease overall coverage
3. **Update Documentation**: Keep this guide current
4. **Run Full Suite**: Ensure all tests pass before PR
5. **Performance Check**: Verify no significant regressions

For questions about testing practices, refer to this guide or ask in the project discussions.