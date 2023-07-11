"""Configuration file for Sphinx."""
import os
import sys

sys.path.insert(0, os.path.abspath('../../src'))

def setup(app):
    app.add_css_file('css/custom.css')

project = 'ska-ser-scpi'
copyright = '2023, SKAO'
author = 'SKAO'
release = '0.3.1'

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_context = {
    "favicon": "img/favicon_mono.ico",
    "logo": "img/logo.png",
    "theme_logo_only": True,
}

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

nitpick_ignore = [
    ('py:class', 'numpy.number'),
]
