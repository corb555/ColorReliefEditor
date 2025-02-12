# Configuration file for the Sphinx documentation builder.
#
# To build .rst files for ColorReliefEditor modules:
# Go to the projectroot folder (ColorReliefEditor)
# sphinx-apidoc -o docs/source ColorReliefEditor

import os
import sys

# Include the project root and module paths
sys.path.insert(0, os.path.abspath('../..'))

project = 'Color Relief Editor'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode', 'sphinx.ext.napoleon', 'myst_parser',]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
autoclass_content = 'both'

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
