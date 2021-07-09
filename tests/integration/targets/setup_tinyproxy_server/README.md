# `setup_tinyproxy_server`
Responsible for installing and running a `tinyproxy` server.

## Notes
* Installs `tinyproxy` via the `ansible.builtin.package` module, which will in turn require the correct packaging module and its required libraries to be available. On MacOS that means the [`community.general` collection](https://galaxy.ansible.com/community/general) is required for homebrew support.
