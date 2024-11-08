# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "access_amherst_backend"
copyright = "2024, Dhyey Mavani, Liam Davis, Ryan Ji, Shreya Hegde, Thu Hoang"
author = "Dhyey Mavani, Liam Davis, Ryan Ji, Shreya Hegde, Thu Hoang"
release = "0.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
]

templates_path = ["_templates"]
exclude_patterns = []

language = "python"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["../build/html/_static"]

# set up Django environment
import os
import sys
import django

sys.path.insert(0, os.path.abspath("../../access_amherst_backend"))
os.environ["DJANGO_SETTINGS_MODULE"] = "access_amherst_backend.settings"
django.setup()
