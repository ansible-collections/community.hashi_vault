# community.hashi_vault Collection
<!-- Add CI and code coverage badges here. Samples included below. -->
[![CI](https://github.com/ansible-collections/community.hashi_vault/workflows/CI/badge.svg?event=push)](https://github.com/ansible-collections/community.hashi_vault/actions) [![Codecov](https://img.shields.io/codecov/c/github/ansible-collections/community.hashi_vault)](https://codecov.io/gh/ansible-collections/community.hashi_vault)

<!-- Describe the collection and why a user would want to use it. What does the collection do? -->
## Collection Documentation

Browsing the [**latest** collection documentation](https://docs.ansible.com/ansible/latest/collections/community/hashi_vault) will show docs for the _latest version released in the Ansible package_ not the latest version of the collection released on Galaxy.

Browsing the [**devel** collection documentation](https://docs.ansible.com/ansible/devel/collections/community/hashi_vault) shows docs for the _latest version released on Galaxy_.

If you use the Ansible package and don't update collections independently, use **latest**, if you install or update this collection directly from Galaxy, use **devel**. If you are looking to contribute, use **devel**.
## Tested with Ansible

* 2.9
* 2.10
* 2.11
* devel (latest development commit)

See [the CI configuration](https://github.com/ansible-collections/community.hashi_vault/blob/main/.github/workflows/ansible-test.yml) for the most accurate testing information.
<!-- List the versions of Ansible the collection has been tested with. Must match what is in galaxy.yml. -->

## Tested with Vault

We currently test against the latest two minor versions of Vault major version `1`. The patch version within each minor will be updated periodically.

We do not test against any versions of Vault with major version `0`.

If/when a new major version of Vault is released, we'll revisit which versions to test against.

The decision of which version(s) of Vault to test against is still somewhat in flux, as we try to balance wide testing with CI execution time and resources.

See [the CI configuration](https://github.com/ansible-collections/community.hashi_vault/blob/main/.github/workflows/ansible-test.yml) for the most accurate testing information.

## Python Requirements

**[Support for Python 2 & Python 3.5 will be dropped in `v2.0.0` of the collection.](https://github.com/ansible-collections/community.hashi_vault/issues/81)**

Currently we test against Python versions:
* 2.7
* 3.5
* 3.6
* 3.7
* 3.8
* 3.9
* 3.10 (support not yet guaranteed)


## External requirements

**NOTE:** `hvac` versions `0.10.12` and `0.10.13` inadvertently did not work with Python 2.

  - `hvac` (python library)
    - `hvac` 0.7.0+ (for namespace support)
    - `hvac` 0.9.6+ (to avoid all deprecation warnings)
    - `hvac` 0.10.5+ (for JWT auth support)
    - `hvac` 0.10.6+ (to avoid deprecation warning for AppRole)
  - `botocore` (only if inferring aws params from boto)
  - `boto3` (only if using a boto profile)

## Included content

- Lookup Plugins
  - `hashi_vault`

## Using this collection

<!--Include some quick examples that cover the most common use cases for your collection content. -->

See [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing to this collection

See the contributor guide in the [**devel** collection documentation](https://docs.ansible.com/ansible/devel/collections/community/hashi_vault).

<!--Describe how the community can contribute to your collection. At a minimum, include how and where users can create issues to report problems or request features for this collection.  List contribution requirements, including preferred workflows and necessary testing, so you can benefit from community PRs. If you are following general Ansible contributor guidelines, you can link to - [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html). -->

## Releasing this collection (for maintainers)
[Follow the instructions for releasing small collections in the Ansible community wiki](https://github.com/ansible/community/wiki/ReleasingCollections#releasing-without-release-branches-for-smaller-collections).

Once the new collection is published and the Zuul job is finished, add a release in GitHub by [manually running the `GitHub Release` workflow](https://github.com/ansible-collections/community.hashi_vault/actions/workflows/github-release.yml). You'll need to enter the version number, which should exactly match the tag used to release the collection.

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
