#!/usr/bin/env python3
"""
Test runner for sp-quiz tests. 
Note:- {Only Phase 1 & 2 Tests Included for Now}

This script runs all unit, integration, and benchmark tests with a
structured summary.  Pass --type to narrow execution scope.

Usage::

    python run_tests.py                # run everything
    python run_tests.py --type unit
    python run_tests.py --type integration
    python run_tests.py --type benchmarks
    python run_tests.py -q             # minimal output
"""

import unittest
import sys
import os
from io import StringIO
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_tests(verbosity=2, pattern='test_*.py'):
    """
    Run all tests matching the pattern.
    
    Args:
        verbosity: Level of test output detail (0-2)
        pattern: Pattern to match test files
    
    Returns:
        TestResult object
    """
    # Discover tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern=pattern)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result


def print_summary(result):
    """
    Print test summary.
    
    Args:
        result: TestResult object
    """
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("="*70)
    
    if result.wasSuccessful():
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    
    print("="*70)


def run_unit_tests():
    """Run only unit tests."""
    print("\n" + "="*70)
    print("RUNNING UNIT TESTS")
    print("="*70 + "\n")
    
    # Run tests for each module
    test_modules = [
        #phase1
        'test_card',
        'test_review',
        'test_user',
        'test_exceptions',
        'test_storage',
        #auto-qualityreview generation
        'test_quality_scorer.py',
        #Phase2
        'test_sm2_plus',
        'test_scheduler',
        'test_utils'
    ]
    
    total_result = unittest.TestResult()
    
    for module_name in test_modules:
        print(f"\n--- Testing {module_name} ---")
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(module_name)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Aggregate results
        total_result.testsRun += result.testsRun
        total_result.failures.extend(result.failures)
        total_result.errors.extend(result.errors)
        total_result.skipped.extend(result.skipped)
    
    return total_result


def run_integration_tests():
    """Run only integration tests."""
    print("\n" + "="*70)
    print("RUNNING INTEGRATION TESTS")
    print("="*70 + "\n")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test_integration')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

def run_benchmark_tests():
    """Run Phase 2 performance benchmarks."""
    print("\n" + "="*70)
    print("RUNNING BENCHMARK / PERFORMANCE TESTS (Phase 2)")
    print("="*70 + "\n")

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test_benchmarks')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result

def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run sp-quiz Phase 1 tests')
    parser.add_argument(
        '--type',
        choices=['all', 'unit', 'integration', 'benchmarks'],
        default='all',
        help='Type of tests to run (default: all)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='count',
        default=2,
        help='Increase verbosity'
    )
    parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Minimal output'
    )
    
    args = parser.parse_args()
    
    verbosity = 0 if args.quiet else args.verbose
    
    print("="*70)
    print("SP-QUIZ PHASE 1&2 TEST SUITE")
    print("="*70)
    
    if args.type == 'all':
        result = run_tests(verbosity=verbosity)
    elif args.type == 'unit':
        result = run_unit_tests()
    elif args.type == 'integration':
        result = run_integration_tests()
    elif args.type == 'benchmarks':
        result = run_benchmark_tests()
    
    print_summary(result)
    
    
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
