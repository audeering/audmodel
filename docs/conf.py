from datetime import date
import os
import shutil

import toml

import audeer


config = toml.load(audeer.path("..", "pyproject.toml"))


# Project -----------------------------------------------------------------
project = config["project"]["name"]
author = ", ".join(author["name"] for author in config["project"]["authors"])
copyright = f"2019-{date.today().year} audEERING GmbH"
version = audeer.git_repo_version()
title = "Documentation"


# General -----------------------------------------------------------------
master_doc = "index"
source_suffix = ".rst"
exclude_patterns = [
    "api-src",
    "build",
    "tests",
    "Thumbs.db",
    ".DS_Store",
]
templates_path = ["_templates"]
pygments_style = None
extensions = [
    "jupyter_sphinx",  # executing code blocks
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # support for Google-style docstrings
    "sphinx.ext.autosummary",
    "sphinx_autodoc_typehints",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinx_copybutton",  # for "copy to clipboard" buttons
]
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "audbackend": ("https://audeering.github.io/audbackend/", None),
    "audfactory": ("https://audeering.github.io/audfactory/", None),
    "filelock": ("https://py-filelock.readthedocs.io/en/latest/", None),
}
# Disable Gitlab as we need to sign in
linkcheck_ignore = [
    "https://gitlab.audeering.com",
    "http://sphinx-doc.org",
]
# Ignore package dependencies during building the docs
autodoc_mock_imports = [
    "audiofile",
    "audsp",
    "numpy",
    "pandas",
    "tqdm",
]
# Reference with :ref:`data-header:Database`
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 2
# Select only code from example ceels
copybutton_prompt_text = r">>> |\.\.\. "
copybutton_prompt_is_regexp = True

# Disable auto-generation of TOC entries in the API
# https://github.com/sphinx-doc/sphinx/issues/6316
toc_object_entries = False


# HTML --------------------------------------------------------------------
html_theme = "sphinx_audeering_theme"
html_theme_options = {
    "display_version": True,
    "logo_only": False,
}
html_title = title
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]


# Copy API (sub-)module RST files to docs/api/ folder ---------------------
audeer.rmdir("api")
audeer.mkdir("api")
api_src_files = audeer.list_file_names("api-src")
api_dst_files = [
    audeer.path("api", os.path.basename(src_file)) for src_file in api_src_files
]
for src_file, dst_file in zip(api_src_files, api_dst_files):
    shutil.copyfile(src_file, dst_file)
