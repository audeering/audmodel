from subprocess import check_output

import graphviz


# Project -----------------------------------------------------------------
project = 'audmodel'
copyright = '2019-2020 audEERING GmbH'
author = 'Hagen Wierstorf'
# The x.y.z version read from tags
try:
    version = check_output(['git', 'describe', '--tags', '--always'])
    version = version.decode().strip()
except Exception:
    version = '<unknown>'
title = '{} Documentation'.format(project)


# General -----------------------------------------------------------------
master_doc = 'index'
extensions = []
source_suffix = '.rst'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
pygments_style = None
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # support for Google-style docstrings
    'sphinx_autodoc_typehints',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosectionlabel',
    'nbsphinx',
]
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://docs.scipy.org/doc/numpy/', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/stable/', None),
}
# Disable Gitlab as we need to sign in
linkcheck_ignore = [
    'https://gitlab.audeering.com',
]
# Ignore package dependencies during building the docs
autodoc_mock_imports = [
    'numpy',
    'pandas',
    'tqdm',
]
# Reference with :ref:`data-header:Database`
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 2
# Disable auto-build of Jupyter notebooks
nbsphinx_execute = 'never'
# This is processed by Jinja2 and inserted before each Jupyter notebook
nbsphinx_prolog = r"""
{% set docname = env.doc2path(env.docname, base='docs') %}
{% set base_url = "https://gitlab.audeering.com/tools/audmodel/raw" %}

.. role:: raw-html(raw)
    :format: html

:raw-html:`<div class="notebook"><a href="{{ base_url }}/{{ env.config.version }}/{{ docname }}?inline=false"> Download notebook: {{ docname }}</a></div>`
"""  # noqa: E501
nbsphinx_timeout = 3600

# HTML --------------------------------------------------------------------
html_theme = 'sphinx_audeering_theme'
html_theme_options = {
    'display_version': True,
    'logo_only': False,
}
html_title = title


# Graphviz figures --------------------------------------------------------
dot_files = [
    './pics/workflow.dot',
]
for dot_file in dot_files:
    graphviz.render('dot', 'svg', dot_file)
