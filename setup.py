"""
Compatibility shim — all project metadata is declared in :file:`pyproject.toml`
(PEP 621). This file remains so ``pip install -e .`` works on older toolchains.
"""

from setuptools import setup

setup()
