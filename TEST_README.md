# Data Processing Pipeline Test Suite

This comprehensive test suite validates the functionality of your AI-powered data processing pipeline without making actual API calls to avoid costs and dependencies.

## 🧪 What's Tested

### Core Functionality
- **Data Loading**: Excel file to DataFrame conversion
- **Data Processing**: JSON conversion, token validation, chunking logic
- **AI Response Handling**: Response parsing and cleaning (mocked)
- **Output Generation**: Excel file creation with versioning
- **Configuration**: Model selection, API mode switching
- **Error Handling**: Graceful failure handling

### Test Coverage Areas

1. **`TestDataProcessingPipeline`** - Main class functionality
   - Initialization and configuration
   - File I/O operations
   - Token limit calculations and validation
   - Chunk size optimization
   - Response processing
   - Output file generation

2. **`TestUtilityFunctions`** - Helper functions
   - Time formatting
   - API mode switching
   - Model configuration

3. **`TestTextSplitter`** - Data chunking
   - DataFrame splitting logic
   - Edge cases (empty data, large chunks)

4. **`TestAsyncProcessing`** - Async functionality
   - Async chunk processing (mocked)
   - Rate limiting simulation

## 🚀 Running the Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r test_requirements.txt
```

### Basic Test Run

```bash
# Run all tests with basic output
python run_tests.py

# Or run the test file directly
python test_data_processing.py
```

### Advanced Options

```bash
# Run with detailed verbose output
python run_tests.py --verbose

# Run with coverage analysis
python run_tests.py --coverage

# Run with both coverage and verbose output
python run_tests.py --coverage --verbose

# Check if all dependencies are installed
python run_tests.py --check-deps
```

### Coverage Analysis

When running with `--coverage`, the test suite will:
1. Generate a text coverage report in the terminal
2. Create an HTML coverage report in the `htmlcov/` directory
3. Show which lines of code are covered by tests

## 📊 Understanding Test Results

### Success Output
```
🧪 Data Processing Pipeline Test Suite
========================================
✅ All dependencies are available!
🧪 Running basic tests...

test_initialization (test_data_processing.TestDataProcessingPipeline) ... ok
test_convert_to_dataframe (test_data_processing.TestDataProcessingPipeline) ... ok
[... more tests ...]

============================================================
📋 TEST SUMMARY
============================================================
Tests run: 25
Failures: 0
Errors: 0
Success rate: 100.0%
============================================================
✅ All tests passed!
```

### Failure Output
If tests fail, you'll see detailed information about what went wrong:
```
❌ FAILURES (1):
   • test_convert_to_dataframe (test_data_processing.TestDataProcessingPipeline)

🚨 ERRORS (0):

❌ Some tests failed. See details above.
```

## 🔧 Test Structure

### Mock Strategy
The tests use **mocking** to avoid:
- Making actual API calls to Gemini/Vertex AI (saves costs)
- Requiring API keys for testing
- Network dependencies
- Long test execution times

### Test Data
Tests use **temporary files** and **sample data** that are:
- Created fresh for each test
- Automatically cleaned up after tests
- Representative of real data structures

### Key Mocked Components
- **AI API responses**: Simulated with predefined JSON responses
- **Token counting**: Mocked to return controlled values
- **File operations**: Use temporary directories
- **Network calls**: Completely avoided

## 🛠️ Customizing Tests

### Adding New Tests

1. Add new test methods to existing test classes:
```python
def test_new_functionality(self):
    """Test description."""
    # Your test code here
    self.assertEqual(expected, actual)
```

2. Create new test classes for major new features:
```python
class TestNewFeature(unittest.TestCase):
    def setUp(self):
        # Setup code
        pass
    
    def test_feature_behavior(self):
        # Test code
        pass
```

### Modifying Test Data

Update the sample data in `setUp()` methods:
```python
self.sample_data = {
    'ID': [1, 2, 3, 4, 5],
    'Name': ['Item A', 'Item B', 'Item C', 'Item D', 'Item E'],
    # Add your columns here
}
```

## 🔍 Troubleshooting

### Common Issues

**"Module not found" errors:**
```bash
# Install missing dependencies
pip install -r test_requirements.txt
```

**"Permission denied" on temporary files:**
- The test suite cleans up temporary files automatically
- On Windows, antivirus may interfere - add an exception for the test directory

**Tests pass but code fails in production:**
- Tests use mocked API responses
- Verify your API keys and configuration in `.env`
- Check that your input files match the expected format

### Environment Issues

The tests are designed to work with:
- Python 3.8+
- Windows/Linux/macOS
- No API keys required for testing

## 📈 Interpreting Coverage Reports

### Text Coverage Report
```
Name               Stmts   Miss  Cover   Missing
------------------------------------------------
ai.py                150     25    83%   45-50, 78-82
run_script.py         89     30    66%   120-140, 200-210
text_splitter.py       8      0   100%
------------------------------------------------
TOTAL                247     55    78%
```

- **Stmts**: Total lines of code
- **Miss**: Lines not covered by tests
- **Cover**: Percentage covered
- **Missing**: Specific line numbers not tested

### HTML Coverage Report
Open `htmlcov/index.html` in your browser for:
- Visual line-by-line coverage
- Interactive exploration of uncovered code
- Detailed per-file reports

## 🎯 Best Practices

1. **Run tests before committing code changes**
2. **Add tests for new features**
3. **Keep test data small and focused**
4. **Use meaningful test names that describe the behavior**
5. **Mock external dependencies**
6. **Clean up resources in `tearDown()` methods**

## 📞 Support

If you encounter issues with the test suite:
1. Check the console output for specific error messages
2. Verify all dependencies are installed
3. Ensure temporary directories have write permissions
4. Review the test code to understand expected behavior

The test suite is designed to be reliable and informative - any failures likely indicate real issues that should be addressed before running the production pipeline. 