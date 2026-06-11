"""Test fixture/mock implementation package.

A marker file that lets pytest recognize the directory as a package. No import side effects.
Holds hardware/external-resource mock skeletons (`_TEMPLATE_*.py`). Fixture wiring is handled by
`tests/conftest.py`, and this directory keeps only the mock class implementations.
"""
