#!/usr/bin/env python3
"""
Test runner script for the Survey Data System.

This script provides convenient commands for running tests with various configurations.

Usage:
    python run_tests.py                  # Run all tests
    python run_tests.py --unit           # Run only unit tests
    python run_tests.py --integration    # Run only integration tests
    python run_tests.py --coverage       # Run with coverage report
    python run_tests.py --fast           # Skip slow tests
    python run_tests.py --verbose        # Verbose output
"""

import sys
import subprocess
import argparse


def run_pytest(args_list):
    """Run pytest with given arguments."""
    cmd = ['pytest'] + args_list
    print(f"Running: {' '.join(cmd)}")
    print("-" * 80)
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Run tests for Survey Data System')

    parser.add_argument('--unit', action='store_true',
                       help='Run only unit tests')
    parser.add_argument('--integration', action='store_true',
                       help='Run only integration tests')
    parser.add_argument('--e2e', action='store_true',
                       help='Run only end-to-end tests')
    parser.add_argument('--db', action='store_true',
                       help='Run only database tests')
    parser.add_argument('--api', action='store_true',
                       help='Run only API tests')

    parser.add_argument('--coverage', action='store_true',
                       help='Generate coverage report')
    parser.add_argument('--html', action='store_true',
                       help='Generate HTML coverage report')
    parser.add_argument('--fast', action='store_true',
                       help='Skip slow tests')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('-vv', '--very-verbose', action='store_true',
                       help='Very verbose output')
    parser.add_argument('--parallel', action='store_true',
                       help='Run tests in parallel')

    parser.add_argument('path', nargs='?',
                       help='Specific test file or directory to run')

    args = parser.parse_args()

    # Build pytest arguments
    pytest_args = []

    # Test selection
    if args.unit:
        pytest_args.extend(['-m', 'unit'])
    elif args.integration:
        pytest_args.extend(['-m', 'integration'])
    elif args.e2e:
        pytest_args.extend(['-m', 'e2e'])
    elif args.db:
        pytest_args.extend(['-m', 'db'])
    elif args.api:
        pytest_args.append('tests/integration/api/')

    # Speed options
    if args.fast:
        pytest_args.extend(['-m', 'not slow'])

    # Verbosity
    if args.verbose:
        pytest_args.append('-v')
    elif args.very_verbose:
        pytest_args.append('-vv')

    # Coverage
    if args.coverage or args.html:
        pytest_args.append('--cov=.')
        if args.html:
            pytest_args.extend([
                '--cov-report=html',
                '--cov-report=term-missing'
            ])
        else:
            pytest_args.extend([
                '--cov-report=term-missing',
                '--cov-report=xml'
            ])

    # Parallel execution
    if args.parallel:
        pytest_args.extend(['-n', 'auto'])

    # Specific path
    if args.path:
        pytest_args.append(args.path)

    # If no specific flags, add some default useful options
    if not any([args.unit, args.integration, args.e2e, args.db, args.api, args.path]):
        pytest_args.append('-v')

    # Run tests
    exit_code = run_pytest(pytest_args)

    # Print summary
    print("\n" + "=" * 80)
    if exit_code == 0:
        print("✓ All tests passed!")
        if args.html:
            print("\nCoverage report generated: htmlcov/index.html")
    else:
        print("✗ Some tests failed!")
        return exit_code

    return 0


if __name__ == '__main__':
    sys.exit(main())
