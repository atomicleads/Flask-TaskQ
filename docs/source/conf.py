# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from datetime import datetime

import tomlkit
from pallets_sphinx_themes import ProjectLink

sys.path.insert(0, os.path.abspath("."))


def _get_project_meta():
    with open("../../pyproject.toml") as pyproject:
        file_contents = pyproject.read()

    return tomlkit.parse(file_contents)["tool"]["poetry"]  # type: ignore


def _make_copyright(name: str, start_year: int = 2020) -> str:
    end_year = datetime.now().year
    if start_year == end_year:
        return f"{start_year}, {name}"
    return f"{start_year}-{end_year}, {name}"


pkg_meta = _get_project_meta()

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Flask-TaskQ"
copyright = _make_copyright("Ivan Fedorov")
author = "Ivan Fedorov"
release = str(pkg_meta["version"])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx_autodoc_typehints",
    "pallets_sphinx_themes",
]

# Make sure the target is unique
autosectionlabel_prefix_document = True

# Set `typing.TYPE_CHECKING` to `True`:
# https://pypi.org/project/sphinx-autodoc-typehints/
set_type_checking_flag = False
always_document_param_types = False

templates_path = ["_templates"]
# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "flask"
html_theme_options = {"index_sidebar_logo": False}
html_static_path = ["_static"]

html_context = {
    "project_links": [
        ProjectLink("PyPI releases", "https://pypi.org/project/Flask-TaskQ/"),
        ProjectLink(
            "Source Code", "https://github.com/TitaniumHocker/Flask-TaskQ/"
        ),
        ProjectLink(
            "Issue Tracker",
            "https://github.com/TitaniumHocker/Flask-TaskQ/issues/",
        ),
    ]
}

# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    "index": ["project.html", "localtoc.html", "searchbox.html"],
    "**": ["localtoc.html", "relations.html", "searchbox.html"],
}
singlehtml_sidebars = {"index": ["project.html", "localtoc.html"]}
