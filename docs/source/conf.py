# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys


sys.path.insert(0, os.path.abspath('../../src'))

project = 'Gravitas Sandbox Engine'
copyright = '2026, Miron'
author = 'Miron'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',     # Вытягивает докстринги из кода
    'sphinx.ext.napoleon',    # Понимает Google-стиль докстрингов
    'sphinx.ext.viewcode',    # Добавляет ссылки на исходный код
]

templates_path = ['_templates']
exclude_patterns = []

language = 'ru'

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    'private-members': True,
    'special-members': '__init__',
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
