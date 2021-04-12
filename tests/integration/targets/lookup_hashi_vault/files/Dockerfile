FROM quay.io/ansible/default-test-container:3.2.2

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    unzip tinyproxy curl && \
    apt-get clean

RUN git clone https://github.com/ansible-collections/community.hashi_vault.git /opt/c.hv && \
    cd /opt/c.hv/tests/integration/targets && \
    ansible localhost ansible -m include_role -a "name=setup_vault_download" -e vault_base_path=/opt/vault
