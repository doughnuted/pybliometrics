"""Sphinx configuration."""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pybliometrics

sys.path.append(str(Path("..").resolve()))
autodoc_mock_imports = ["_tkinter"]

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "source"))
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
project_copyright = (
    f"2017-{datetime.now(tz=timezone.utc).year} Michael E. Rose and John Kitchin"
)
author = "Michael E. Rose and John Kitchin"
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
latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    # The font size ('10pt', '11pt' or '12pt').
    # Additional stuff for the LaTeX preamble.
    # Latex figure (float) alignment
}

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
