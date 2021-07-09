# `setup_vault_server_download`
This role downloads a specified version of Vault and sets `vault_cmd` to the full path of the binary.

## Notes
* Installs `unzip` via the `ansible.builtin.package` module, which will in turn require the correct packaging module and its required libraries to be available. MacOS is assumed to have `unzip` already.
