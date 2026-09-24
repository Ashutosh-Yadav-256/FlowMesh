"""
Unit tests for FlowMesh AI-Assisted Scripting Engine & API
Tests multi-language script generation, security guardrails, static AST validation,
and automated error remediation.
"""

import pytest
from flowmesh_ai_scripting.engine import (
    AiScriptingEngine,
    ScriptGenerationRequest,
    ScriptLanguage,
    ai_scripting_engine,
)


def test_script_safety_guardrails_powershell():
    engine = AiScriptingEngine()

    # Dangerous: Format volume
    bad_code = "Get-Disk | Clear-Disk -RemoveData; Format-Volume -DriveLetter D"
    val_bad = engine.validate_script_safety(bad_code, ScriptLanguage.POWERSHELL)
    assert val_bad.is_safe is False
    assert val_bad.risk_score > 0.5
    assert any("Volume formatting" in r for r in val_bad.detected_risks)

    # Safe: Service restart with error handling
    safe_code = "Restart-Service -Name 'wuauserv' -Force"
    val_safe = engine.validate_script_safety(safe_code, ScriptLanguage.POWERSHELL)
    assert val_safe.is_safe is True
    assert val_safe.risk_score == 0.0


def test_script_safety_guardrails_bash_and_sql():
    engine = AiScriptingEngine()

    # Dangerous Bash: rm -rf /
    bad_bash = "rm -rf /var/log/*; rm -rf /"
    val_bash = engine.validate_script_safety(bad_bash, ScriptLanguage.BASH)
    assert val_bash.is_safe is False
    assert any("Recursive deletion" in r for r in val_bash.detected_risks)

    # Dangerous SQL: DROP DATABASE
    bad_sql = "DROP DATABASE production_billing; DROP TABLE users;"
    val_sql = engine.validate_script_safety(bad_sql, ScriptLanguage.SQL)
    assert val_sql.is_safe is False
    assert any("Dropping database" in r for r in val_sql.detected_risks)

    # Safe SQL: Selective query
    safe_sql = "SELECT id, name FROM customers WHERE active = true LIMIT 50;"
    val_safe_sql = engine.validate_script_safety(safe_sql, ScriptLanguage.SQL)
    assert val_safe_sql.is_safe is True


def test_script_safety_python_ast():
    engine = AiScriptingEngine()

    # Dangerous Python: eval and exec
    bad_py = "import os\neval('__import__(\"os\").system(\"whoami\")')"
    val_py = engine.validate_script_safety(bad_py, ScriptLanguage.PYTHON)
    assert val_py.is_safe is False
    assert any("eval" in r for r in val_py.detected_risks)

    # Safe Python
    safe_py = "def add(a: int, b: int) -> int:\n    return a + b\n"
    val_safe_py = engine.validate_script_safety(safe_py, ScriptLanguage.PYTHON)
    assert val_safe_py.is_safe is True


def test_ai_script_generation_powershell():
    req = ScriptGenerationRequest(
        prompt="Restart the print spooler service and output status",
        language=ScriptLanguage.POWERSHELL,
        parameters={"service_name": "Spooler"},
    )
    res = ai_scripting_engine.generate_script(req)
    assert "Restart-Service" in res.code
    assert "Spooler" in res.code
    assert res.safety.is_safe is True
    assert res.language == ScriptLanguage.POWERSHELL


def test_ai_script_generation_python_and_ansible():
    # Python
    req_py = ScriptGenerationRequest(
        prompt="Clean and filter null values from input dataset",
        language=ScriptLanguage.PYTHON,
        parameters={"payload": [1, None, 3, None, 5]},
    )
    res_py = ai_scripting_engine.generate_script(req_py)
    assert "def execute_task" in res_py.code
    assert res_py.safety.is_safe is True

    # Ansible Playbook
    req_ans = ScriptGenerationRequest(
        prompt="Ensure nginx web service is started across hosts",
        language=ScriptLanguage.ANSIBLE,
    )
    res_ans = ai_scripting_engine.generate_script(req_ans)
    assert "ansible.builtin.service" in res_ans.code
    assert res_ans.safety.is_safe is True


def test_ai_script_explanation_and_remediation():
    engine = AiScriptingEngine()
    faulty_ps = "Get-ChildItem -Path C:\\logs -ForceTrue"
    error = "Cannot find a parameter with name 'ForceTrue'"

    explanation = engine.explain_and_fix_script(
        code=faulty_ps,
        language=ScriptLanguage.POWERSHELL,
        error_message=error,
    )

    assert "Cannot find a parameter" in explanation.summary
    assert explanation.fixed_code is not None
    assert "-Force" in explanation.fixed_code
    assert explanation.fix_explanation is not None
