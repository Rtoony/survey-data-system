"""
Test Suite for Survey Data System
===================================

This package contains all tests for the survey data system application.

Test Organization:
- test_factory.py: Tests for application factory pattern
- test_extensions.py: Tests for Flask extensions (CORS, Cache)
- unit/: Unit tests for individual modules
- integration/: Integration tests with database
- fixtures/: Test data and fixtures

All tests use mocked database connections to prevent network calls.
Use the mock_db fixture to ensure no real database connections are made.
"""
