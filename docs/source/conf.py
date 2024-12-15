# Configuration file for the Sphinx documentation builder.
#
# To build .rst files for ColorReliefEditor modules:
# Go to the projectroot folder (ColorReliefEditor)
# sphinx-apidoc -o docs/source ColorReliefEditor

import os
import sys

sys.path.insert(0, os.path.abspath('../../ColorReliefEditor'))

project = 'Color Relief Editor'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode', 'sphinx.ext.napoleon']

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
