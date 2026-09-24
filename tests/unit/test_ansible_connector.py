"""
Unit tests for FlowMesh Ansible Connector
Tests 4-point verification, playbook execution, ad-hoc modules, and facts discovery.
"""

import pytest
from flowmesh_connector.protocol import ConnectionSpec, Operation
from connectors.ansible.connector import AnsibleConnector


@pytest.fixture
def ansible_conn_spec() -> ConnectionSpec:
    return ConnectionSpec(
        id="conn_ansible_test",
        tenant_id="tenant_acme",
        type="ansible",
        name="Acme Corporate Ansible Automation Controller",
        config={
            "control_node": "ansible-ctrl.corp.acme.local",
            "inventory_source": "inventories/production.yaml",
            "vault_id": "prod-vault",
        },
        credentials={
            "ssh_private_key": "-----BEGIN OPENSSH PRIVATE KEY-----\nMOCK_KEY\n-----END OPENSSH PRIVATE KEY-----",
            "vault_password": "SuperSecretVaultPassword123!",
        },
        agent_id=None,
    )


@pytest.mark.asyncio
async def test_ansible_conformance(ansible_conn_spec: ConnectionSpec):
    connector = AnsibleConnector()
    assert connector.type == "ansible"

    # 4-point verification
    test_res = await connector.test(ansible_conn_spec)
    assert test_res.success is True
    assert len(test_res.steps) == 4
    step_names = [s.name for s in test_res.steps]
    assert any("Control Node Reachability" in name for name in step_names)
    assert any("Inventory Parsing" in name for name in step_names)
    assert any("Vault & Credential Verification" in name for name in step_names)
    assert any("Core Module Discovery" in name for name in step_names)

    # Schema discovery
    graph = await connector.discover(ansible_conn_spec)
    table_names = [t.table_name for t in graph.entities]
    assert "playbooks" in table_names
    assert "inventories" in table_names
    assert "modules" in table_names


@pytest.mark.asyncio
async def test_ansible_operations(ansible_conn_spec: ConnectionSpec):
    connector = AnsibleConnector()

    # 1. Run Playbook
    op_pb = Operation(
        id="op_ans_1",
        name="run_playbook",
        parameters={
            "playbook": "site.yml",
            "extra_vars": {"target_env": "production"},
            "tags": ["web", "db"],
            "check_mode": False,
        },
    )
    res_pb = await connector.execute(ansible_conn_spec, op_pb)
    assert res_pb.success is True
    assert res_pb.data["status"] == "SUCCESS"
    assert res_pb.data["recap"]["ok"] >= 1
    assert "PLAY RECAP" in res_pb.data["execution_log"]

    # 2. Execute Ad-hoc Module
    op_mod = Operation(
        id="op_ans_2",
        name="execute_module",
        parameters={
            "module_name": "ansible.builtin.service",
            "module_args": {"name": "nginx", "state": "restarted"},
            "host_pattern": "webservers",
        },
    )
    res_mod = await connector.execute(ansible_conn_spec, op_mod)
    assert res_mod.success is True
    assert res_mod.data["changed"] is True
    assert "web-01" in res_mod.data["results"]

    # 3. Get Facts
    op_facts = Operation(
        id="op_ans_3",
        name="get_facts",
        parameters={"host": "db-01.corp.acme.local"},
    )
    res_facts = await connector.execute(ansible_conn_spec, op_facts)
    assert res_facts.success is True
    assert "ansible_facts" in res_facts.data
    assert res_facts.data["ansible_facts"]["ansible_distribution"] == "RedHat"

    # 4. Check Syntax
    op_syntax = Operation(
        id="op_ans_4",
        name="check_syntax",
        parameters={"playbook": "rolling_upgrade.yml"},
    )
    res_syntax = await connector.execute(ansible_conn_spec, op_syntax)
    assert res_syntax.success is True
    assert res_syntax.data["syntax_valid"] is True

    # 5. Unsupported Operation error check
    op_err = Operation(id="op_ans_err", name="unsupported_op", parameters={})
    res_err = await connector.execute(ansible_conn_spec, op_err)
    assert res_err.success is False
    assert "Unsupported Ansible operation" in res_err.error
