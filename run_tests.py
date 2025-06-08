#!/usr/bin/env python3
"""
Test Runner Script for Data Processing Pipeline

This script runs comprehensive unit tests for the data processing pipeline
with optional coverage reporting.

Usage:
    python run_tests.py                    # Run basic tests
    python run_tests.py --coverage         # Run tests with coverage report
    python run_tests.py --verbose          # Run tests with detailed output
    python run_tests.py --coverage --verbose  # Both coverage and verbose
"""

import sys
import os
import unittest
import argparse


def run_tests(coverage=False, verbose=False):
    """
    Run the test suite with optional coverage reporting.
    
    Args:
        coverage (bool): Whether to run with coverage analysis
        verbose (bool): Whether to use verbose output
    """
    
    # Set verbosity level
    verbosity = 2 if verbose else 1
    
    if coverage:
        try:
            import coverage
            
            # Start coverage analysis
            cov = coverage.Coverage()
            cov.start()
            
            print("🔍 Running tests with coverage analysis...\n")
            
            # Discover and run tests
            loader = unittest.TestLoader()
            start_dir = os.path.dirname(__file__)
            suite = loader.discover(start_dir, pattern='test_*.py')
            
            runner = unittest.TextTestRunner(verbosity=verbosity)
            result = runner.run(suite)
            
            # Stop coverage and generate report
            cov.stop()
            cov.save()
            
            print(f"\n{'='*60}")
            print("📊 COVERAGE REPORT")
            print(f"{'='*60}")
            
            # Generate coverage report
            cov.report(show_missing=True)
            
            # Generate HTML coverage report
            html_dir = "htmlcov"
            cov.html_report(directory=html_dir)
            print(f"\n📄 Detailed HTML coverage report generated in: {html_dir}/")
            print(f"   Open {html_dir}/index.html in your browser to view it.")
            
        except ImportError:
            print("❌ Coverage module not installed. Install with: pip install coverage")
            print("🔄 Running tests without coverage analysis...\n")
            run_basic_tests(verbosity)
            
    else:
        print("🧪 Running basic tests...\n")
        run_basic_tests(verbosity)


def run_basic_tests(verbosity=1):
    """Run tests without coverage analysis."""
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Print summary
    print_test_summary(result)
    
    return result.wasSuccessful()


def print_test_summary(result):
    """Print a detailed test summary."""
    
    print(f"\n{'='*60}")
    print("📋 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"Success rate: {success_rate:.1f}%")
    
    if result.failures:
        print(f"\n❌ FAILURES ({len(result.failures)}):")
        for test, trace in result.failures:
            print(f"   • {test}")
    
    if result.errors:
        print(f"\n🚨 ERRORS ({len(result.errors)}):")
        for test, trace in result.errors:
            print(f"   • {test}")
    
    print(f"{'='*60}")
    
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. See details above.")


def check_dependencies():
    """Check if required dependencies are available."""
    
    missing_deps = []
    required_modules = [
        'polars',
        'pandas',
        'google.genai',
        'dotenv',
        'tqdm'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_deps.append(module)
    
    if missing_deps:
        print("⚠️  Missing dependencies:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("\n📦 Install missing dependencies with:")
        print("   pip install -r test_requirements.txt")
        return False
    
    return True


def main():
    """Main function to handle command line arguments and run tests."""
    
    parser = argparse.ArgumentParser(
        description="Run unit tests for the data processing pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run basic tests
  python run_tests.py --coverage         # Run with coverage analysis
  python run_tests.py --verbose          # Run with detailed output
  python run_tests.py -cv                # Run with coverage and verbose output
        """
    )
    
    parser.add_argument(
        '-c', '--coverage',
        action='store_true',
        help='Run tests with coverage analysis'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Run tests with verbose output'
    )
    
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check if all required dependencies are installed'
    )
    
    args = parser.parse_args()
    
    print("🧪 Data Processing Pipeline Test Suite")
    print("=" * 40)
    
    # Check dependencies if requested
    if args.check_deps:
        if check_dependencies():
            print("✅ All dependencies are available!")
        else:
            sys.exit(1)
        return
    
    # Check dependencies before running tests
    if not check_dependencies():
        print("\n❌ Cannot run tests due to missing dependencies.")
        sys.exit(1)
    
    # Run tests
    try:
        run_tests(coverage=args.coverage, verbose=args.verbose)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 