"""Sphinx configuration for building the documentation."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pybliometrics

sys.path.append(str(Path(__file__).resolve().parent.parent))
autodoc_mock_imports = ["_tkinter"]
cwd = Path.cwd()
project_root = cwd.parent
sys.path.insert(0, str(Path("source").resolve()))
sys.path.insert(0, str(project_root))

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx_autodoc_defaultargs",
    "sphinx_copybutton",
]
copybutton_prompt_text = ">>> "

source_suffix = ".rst"
master_doc = "index"
project = "pybliometrics"
author = "Michael E. Rose and John Kitchin"

year = datetime.now(tz=datetime.now().astimezone().tzinfo).date().year
COPYRIGHT = f"2017-{year} {author}"
version = pybliometrics.__version__

language = "en"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

pygments_style = "sphinx"
todo_include_todos = False

# Options for HTML output
html_theme = "alabaster"
html_theme_options = {
    "github_user": "pybliometrics-dev",
    "github_repo": "pybliometrics",
    "github_banner": "true",
    "github_button": "true",
    "github_type": "star",
}
html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "searchbox.html",
    ]
}

# Options for HTMLHelp output
html_show_sourcelink = True
htmlhelp_basename = "pybliometricsdoc"
autoclass_content = "both"

# Option to group members of classes
autodoc_member_order = "bysource"

# Type hints
autodoc_typehints = "description"
napoleon_use_param = True
typehints_document_rtype = False
rst_prolog = (
    """
.. |default| raw:: html

    <div class="default-value-section">"""
    ' <span class="default-value-label">Default:</span>'
)

# -- Options for LaTeX output ---------------------------------------------
latex_elements = {}

latex_documents = [
    (master_doc, "pybliometrics.tex", "pybliometrics Documentation", author, "manual"),
]

# Options for manual page output
man_pages = [(master_doc, "pybliometrics", "pybliometrics Documentation", [author], 1)]

# Options for Texinfo output
texinfo_documents = [
    (
        master_doc,
        "pybliometrics",
        "pybliometrics Documentation",
        author,
        "pybliometrics",
        "One line description of project.",
        "Miscellaneous",
    ),
]
