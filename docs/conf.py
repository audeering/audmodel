from subprocess import check_output


# Project -----------------------------------------------------------------
project = 'audmodel'
copyright = '2019-2020 audEERING GmbH'
author = 'Johannes Wagner, Hagen Wierstorf'
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
    'jupyter_sphinx',  # executing code blocks
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # support for Google-style docstrings
    'sphinx_autodoc_typehints',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosectionlabel',
    'sphinx_copybutton',  # for "copy to clipboard" buttons
]
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'audfactory': ('http://tools.pp.audeering.com/audfactory/', None),
}
# Disable Gitlab as we need to sign in
linkcheck_ignore = [
    'https://gitlab.audeering.com',
    'http://sphinx-doc.org',
]
# Ignore package dependencies during building the docs
autodoc_mock_imports = [
    'audiofile',
    'audsp',
    'numpy',
    'pandas',
    'tqdm',
]
# Reference with :ref:`data-header:Database`
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 2
# Select only code from example ceels
copybutton_prompt_text = r'>>> |\.\.\. '
copybutton_prompt_is_regexp = True

# HTML --------------------------------------------------------------------
html_theme = 'sphinx_audeering_theme'
html_theme_options = {
    'display_version': True,
    'logo_only': False,
}
html_title = title
html_static_path = ['_static']
html_css_files = ['css/custom.css']
