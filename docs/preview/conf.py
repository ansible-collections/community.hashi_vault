# This file only contains a selection of the most common options. For a full list see the
# documentation:
# http://www.sphinx-doc.org/en/master/config

project = 'Ansible collections'
copyright = 'Ansible contributors'

title = 'Ansible Collections Documentation'
html_short_title = 'Ansible Collections Documentation'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 'sphinx_antsibull_ext']

pygments_style = 'ansible'

highlight_language = 'YAML+Jinja'

html_theme = 'sphinx_ansible_theme'
html_show_sphinx = False

display_version = False

html_use_smartypants = True
html_use_modindex = False
html_use_index = False
html_copy_source = False

intersphinx_mapping = {
    'python': ('https://docs.python.org/2/', (None, '../python2.inv')),
    'python3': ('https://docs.python.org/3/', (None, '../python3.inv')),
    'jinja2': ('http://jinja.palletsprojects.com/', (None, '../jinja2.inv')),
    'ansible4': ('https://docs.ansible.com/ansible/4/', (None, '../ansible4.inv')),
}

default_role = 'any'

nitpicky = True
