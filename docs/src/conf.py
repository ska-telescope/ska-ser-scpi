"""Configuration file for Sphinx."""
import os
import sys

sys.path.insert(0, os.path.abspath('../../src'))

project = 'ska-ser-scpi'
copyright = '2023, SKAO'
author = 'SKAO'
release = '0.5.0'

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
]

exclude_patterns = []

html_theme = "ska_ser_sphinx_theme"

html_context = {}

# autodoc_mock_imports = [
# ]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.10/", None),
    "ska-ser-devices": (
        "https://developer.skao.int/projects/ska-ser-devices/en/0.1.1/",
        None,
    ),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

nitpicky = True

nitpick_ignore = [
    ('py:class', 'numpy.number'),
]
