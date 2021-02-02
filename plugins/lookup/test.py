# (c) 2021, Brian Scholer (@briantist)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  lookup: test
  author:
    - Brian Scholer (@briantist)
  short_description: test
  description:
    - test
  options:
    val:
      description: test
"""

EXAMPLES = """
"""

from ansible.errors import AnsibleError
# from ansible.module_utils.parsing.convert_bool import boolean
# from ansible import constants as C
from ansible.utils.display import Display

from ansible_collections.community.hashi_vault.plugins.lookup.__init__ import HashiVaultLookupBase
# from ansible_collections.community.hashi_vault.plugins.module_utils.hashi_vault_common import HashiVaultHelper

display = Display()


class LookupModule(HashiVaultLookupBase):
    def run(self, terms, variables=None, **kwargs):

        ret = []

        # opts = kwargs.copy()
        # opts.update(self.parse_term(term))
        # self.set_options(direct=opts)
        self.set_options(direct=kwargs)
        v = self.get_option('val')
        display.warning(type(v).__name__)
        ret = [v]

        return ret
