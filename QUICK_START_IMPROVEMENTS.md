# Quick Start Guide - Code Quality Improvements

## 🚀 Getting Started

### 1. Install Test Dependencies

```bash
cd backend
pip install -r requirements-test.txt
```

### 2. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_performance_tracker.py -v

# Run only unit tests (fast)
pytest tests/ -m unit

# Run with detailed output
pytest tests/ -vv --tb=long
```

### 3. View Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=. --cov-report=html

# Open in browser (Windows)
start htmlcov/index.html

# Open in browser (Linux/Mac)
open htmlcov/index.html
```

---

## 📝 Using the New Features

### Custom Exceptions

```python
from exceptions import (
    PersonaNotFoundError,
    OllamaConnectionError,
    InputTooLongError,
    RateLimitExceededError
)

# Example 1: Persona validation
try:
    tracker = PerformanceTracker(persona_type="invalid")
except PersonaNotFoundError as e:
    print(f"Error: {e.message}")
    print(f"Available personas: {e.available_personas}")

# Example 2: LLM connection error
try:
    llm = OllamaLlm(model="gemma3:4b", base_url="http://localhost:11434")
    response = await llm.generate_content_async(request)
except OllamaConnectionError as e:
    print(f"Cannot connect to Ollama at {e.base_url}")
    print(f"Original error: {e.original_error}")

# Example 3: Input validation
try:
    validate_message(user_input)
except InputTooLongError as e:
    print(f"Message too long: {e.input_length} chars (max: {e.max_length})")
```

### Configuration

```python
from config import config

# Access trust thresholds
if victim_trust >= config.trust.SCAMMER_WIN_THRESHOLD:
    print("Scammer wins!")

# Get persona-specific values
max_change = config.get_max_trust_change("elderly")  # Returns 12
initial_trust = config.get_initial_trust("elderly")  # Returns {"scammer": 70, ...}

# Validate inputs
if config.validate_persona("elderly"):
    print("Valid persona")

if config.validate_scam_tactic("假冒官員詐騙"):
    print("Valid scam tactic")

# Access LLM config
print(f"Model: {config.llm.DEFAULT_MODEL}")
print(f"Temperature: {config.llm.TEMPERATURE}")
print(f"Max retries: {config.llm.MAX_RETRIES}")
```

### Input Validation

```python
from utils.validation import (
    ValidatedMessageRequest,
    SimulationStartRequest,
    rate_limiter
)
from fastapi import APIRouter

router = APIRouter()

# Example 1: Validated message endpoint
@router.post("/message")
async def send_message(request: ValidatedMessageRequest):
    # request.message is already validated:
    # - Length: 1-1000 characters
    # - No prompt injection patterns
    # - Stripped whitespace
    return {"reply": process_message(request.message)}

# Example 2: Simulation start with validation
@router.post("/simulation/start")
async def start_simulation(request: SimulationStartRequest):
    # request.victim_persona is validated against available personas
    # request.scam_tactic is validated against available tactics
    # request.mode is validated (must be "fast" or "demo")
    return {"simulation_id": create_simulation(request)}

# Example 3: Rate limiting
@router.post("/api/endpoint")
async def some_endpoint(request: Request):
    client_ip = request.client.host
    
    if not rate_limiter.check_rate_limit(client_ip):
        retry_after = rate_limiter.get_retry_after(client_ip)
        raise RateLimitExceededError(10, 60, retry_after)
    
    return {"status": "ok"}
```

---

## 🧪 Writing Tests

### Test Structure

```python
import pytest
from utils.performance_tracker import PerformanceTracker
from config import config

class TestYourFeature:
    """Test suite for your feature"""
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        tracker = PerformanceTracker(victim_persona="elderly")
        
        # Act
        result = tracker.analyze_scammer_turn(
            dialogue="我係銀行職員",
            victim_response="係咪真㗎？"
        )
        
        # Assert
        assert result["trust_change"] > 0
        assert "authority" in result["tactics_used"]
    
    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(PersonaNotFoundError) as exc_info:
            PerformanceTracker(victim_persona="invalid")
        
        assert "invalid" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test async function"""
        result = await some_async_function()
        assert result is not None
```

### Using Fixtures

```python
def test_with_fixtures(sample_conversation_history, mock_config):
    """Test using fixtures from conftest.py"""
    # sample_conversation_history is automatically provided
    assert len(sample_conversation_history) == 4
    
    # mock_config is automatically provided
    assert mock_config.trust.SCAMMER_WIN_THRESHOLD == 80
```

---

## 🔧 Configuration Tuning

### Environment Variables

Create `.env` file in project root:

```bash
# Trust System
TRUST_SCAMMER_WIN_THRESHOLD=80
TRUST_EXPERT_WIN_THRESHOLD=75

# LLM Configuration
AGENT_MODEL=gemma3:4b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0.5
OLLAMA_TOP_P=0.85

# Validation
MAX_MESSAGE_LENGTH=1000
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60

# Simulation
MAX_ROUNDS=15
AUTO_TRAIN_ENABLED=true
```

### Programmatic Configuration

```python
from config import config

# Modify at runtime (for testing)
config.trust.SCAMMER_WIN_THRESHOLD = 85
config.simulation.MAX_ROUNDS = 20
config.validation.MAX_MESSAGE_LENGTH = 2000
```

---

## 📊 Running Code Quality Checks

### Format Code

```bash
# Format with black
black backend/

# Sort imports
isort backend/

# Check formatting (without changes)
black backend/ --check
```

### Lint Code

```bash
# Run flake8
flake8 backend/ --max-line-length=100

# Run mypy (type checking)
mypy backend/ --ignore-missing-imports
```

### Full Quality Check

```bash
# Run all checks
black backend/ --check && \
isort backend/ --check && \
flake8 backend/ --max-line-length=100 && \
pytest tests/ --cov=. --cov-report=term
```

---

## 🐛 Debugging Tests

### Run Single Test

```bash
# Run specific test
pytest tests/test_performance_tracker.py::TestTrustInertia::test_high_trust_increase_inertia -v

# Run with print statements
pytest tests/test_performance_tracker.py -v -s

# Run with debugger on failure
pytest tests/test_performance_tracker.py --pdb
```

### View Test Output

```bash
# Verbose output
pytest tests/ -vv

# Show local variables on failure
pytest tests/ -l

# Show full traceback
pytest tests/ --tb=long
```

---

## 📈 Continuous Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
        pip install -r backend/requirements-test.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest tests/ --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
```

---

## 🎯 Best Practices

### 1. Always Validate Input

```python
# ✅ Good
@router.post("/message")
async def send_message(request: ValidatedMessageRequest):
    return process(request.message)

# ❌ Bad
@router.post("/message")
async def send_message(request: dict):
    return process(request["message"])
```

### 2. Use Specific Exceptions

```python
# ✅ Good
if not config.validate_persona(persona):
    raise PersonaNotFoundError(persona, config.persona.AVAILABLE_PERSONAS)

# ❌ Bad
if not config.validate_persona(persona):
    raise Exception(f"Invalid persona: {persona}")
```

### 3. Use Configuration Constants

```python
# ✅ Good
if trust >= config.trust.SCAMMER_WIN_THRESHOLD:
    return "scammer_wins"

# ❌ Bad
if trust >= 80:  # Magic number!
    return "scammer_wins"
```

### 4. Write Tests First (TDD)

```python
# 1. Write test
def test_new_feature():
    result = new_feature()
    assert result == expected

# 2. Run test (should fail)
# pytest tests/test_new_feature.py

# 3. Implement feature
def new_feature():
    return expected

# 4. Run test (should pass)
```

---

## 🆘 Troubleshooting

### Tests Fail with Import Errors

```bash
# Make sure you're in the backend directory
cd backend

# Install test dependencies
pip install -r requirements-test.txt

# Run tests
pytest tests/ -v
```

### Coverage Report Not Generated

```bash
# Install coverage
pip install pytest-cov

# Generate report
pytest tests/ --cov=. --cov-report=html

# Check htmlcov directory
ls htmlcov/
```

### Rate Limiter Not Working

```python
# Make sure middleware is added in main.py
from utils.validation import rate_limit_middleware

app.middleware("http")(rate_limit_middleware)
```

---

## 📚 Additional Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **FastAPI Testing**: https://fastapi.tiangolo.com/tutorial/testing/
- **Python Type Hints**: https://docs.python.org/3/library/typing.html

---

## ✅ Checklist for New Features

Before committing new code:

- [ ] Add type hints to all functions
- [ ] Use config constants (no magic numbers)
- [ ] Add input validation (Pydantic models)
- [ ] Use specific exceptions (not generic Exception)
- [ ] Write unit tests (aim for >80% coverage)
- [ ] Add docstrings to public functions
- [ ] Run `black` and `isort` for formatting
- [ ] Run `pytest` to ensure all tests pass
- [ ] Update documentation if needed

---

**Happy Testing! 🎉**
