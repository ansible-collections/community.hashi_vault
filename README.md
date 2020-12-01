# community.hashi_vault Collection
<!-- Add CI and code coverage badges here. Samples included below. -->
[![CI](https://github.com/ansible-collections/community.hashi_vault/workflows/CI/badge.svg?event=push)](https://github.com/ansible-collections/community.hashi_vault/actions) [![Codecov](https://img.shields.io/codecov/c/github/ansible-collections/community.hashi_vault)](https://codecov.io/gh/ansible-collections/community.hashi_vault)

<!-- Describe the collection and why a user would want to use it. What does the collection do? -->

## Tested with Ansible

<!-- List the versions of Ansible the collection has been tested with. Must match what is in galaxy.yml. -->

## External requirements

  - `hvac` (python library)
    - `hvac` 0.7.0+ (for namespace support)
    - `hvac` 0.9.6+ (to avoid all deprecation warnings)
    - `hvac` 0.10.5+ (for JWT auth support)
  - `botocore` (only if inferring aws params from boto)
  - `boto3` (only if using a boto profile)

## Included content

- Lookup Plugins
  - `hashi_vault`

## Using this collection

<!--Include some quick examples that cover the most common use cases for your collection content. -->

See [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing to this collection

<!--Describe how the community can contribute to your collection. At a minimum, include how and where users can create issues to report problems or request features for this collection.  List contribution requirements, including preferred workflows and necessary testing, so you can benefit from community PRs. If you are following general Ansible contributor guidelines, you can link to - [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html). -->


## Release notes

See the [changelog](https://github.com/ansible-collections/community.hashi_vault/tree/main/CHANGELOG.rst).

## FAQ

### **Q:** Why not have a single collection of HashiCorp products instead of one just for Vault?

**A:** This was considered when the `hashi_vault` plugin was first moved from `community.general` to this collection. There are several reasons behind this:

* The other known HashiCorp content at that time (covering Consul, Nomad, Terraform, etc.) does not share implementation or testing with Vault content.
* The maintainers are also different. This being a community supported collection means separate maintainers are more likely to focus on goals that make sense for their particular plugins and user base.
* The HashiCorp products serve different goals, and even when used together, they have their own APIs and interfaces that don't really have anything in common from the point of view of the Ansible codebase as a consumer.
* It would complicate testing. One of the primary goals of moving to a new collection was the ability to increase the scope of Vault-focused testing without having to balance the impact to unrelated components.
* It makes for a smaller package for consumers, that can hopefully release more quickly.

### **Q:** Why is the collection named `community.hashi_vault` instead of `community.vault` or `community.hashicorp_vault` or `hashicorp.vault` or any number of other names?

**A:** This too was considered during formation. In the end, `hashi_vault` is a compromise of various concerns.

* `hashicorp.vault` looks great, but implies the collection is supported by HashiCorp (which it is not). That doesn't follow the convention of denoting community supported namespaces with `community.`
* `community.vault` looks great at first, but "Vault" is a very general and overloaded term, and in Ansible the first "Vault" one thinks of is [Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html). So in the naming, and even in the future of this collection and its content, we have to be mindful of avoiding and removing ambiguities between these products (and other Vaults out there).
* `community.hashicorp_vault` is descriptive and unambiguous but is unfortunately quite long.
* `community.hashicorp` would be good for a collection that aims to contain community-supported content related to all HashiCorp products, but this collection is only focused on Vault (see above question).
* `community.hashicorp.vault` (or any other 3-component name): not supported (also long).
* `community.hashi_vault` isn't perfect, but has an established convention in the existing plugin name and isn't as long as `hashicorp_vault`.


## Roadmap

<!-- Optional. Include the roadmap for this collection, and the proposed release/versioning strategy so users can anticipate the upgrade/update cycle. -->

## More information

<!-- List out where the user can find additional information, such as working group meeting times, slack/IRC channels, or documentation for the product this collection automates. At a minimum, link to: -->

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Collections Checklist](https://github.com/ansible-collections/overview/blob/master/collection_requirements.rst)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
- [The Bullhorn (the Ansible Contributor newsletter)](https://us19.campaign-archive.com/home/?u=56d874e027110e35dea0e03c1&id=d6635f5420)
- [Changes impacting Contributors](https://github.com/ansible-collections/overview/issues/45)

## Licensing

<!-- Include the appropriate license information here and a pointer to the full licensing details. If the collection contains modules migrated from the ansible/ansible repo, you must use the same license that existed in the ansible/ansible repo. See the GNU license example below. -->

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
