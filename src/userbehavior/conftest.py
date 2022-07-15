import pytest


def pytest_addoption(parser):
    parser.addoption("--integration", dest="integration", action="store_true", help="run with integration tests")
    parser.addoption("--acceptance", dest="acceptance", action="store_true", help="run with acceptance tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "acceptance: mark test as acceptance test")


def pytest_runtest_setup(item):
    if hasattr(item.obj, "acceptance"):
        if not pytest.config.option.acceptance:
            pytest.skip("skipping acceptance test")
    if hasattr(item.obj, "integration"):
        if not pytest.config.option.integration:
            pytest.skip("skipping integration test")

