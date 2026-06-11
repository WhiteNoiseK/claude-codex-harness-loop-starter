"""Integration-test package — verifies interaction across several modules/adapter mocks.

A marker file that lets pytest recognize the directory as a package. No import side effects.
Targeted by the @pytest.mark.integration marker. The env guard is handled by this directory's conftest.py.
"""
