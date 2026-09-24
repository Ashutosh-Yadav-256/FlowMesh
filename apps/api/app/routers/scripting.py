"""
FlowMesh AI-Assisted Scripting API Router
Provides endpoints for AI script generation, safety validation, and automated remediation.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import CurrentAuth
from flowmesh_auth.rbac import is_allowed
from flowmesh_ai_scripting.engine import (
    ai_scripting_engine,
    ScriptGenerationRequest,
    ScriptGenerationResult,
    ScriptValidationResult,
    ScriptExplanationResult,
    ScriptLanguage,
)

router = APIRouter(prefix="/api/v1/scripting", tags=["AI-Assisted Scripting"])


def enforce_rbac(auth: CurrentAuth, resource: str, action: str) -> None:
    if not is_allowed(auth.role, resource, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"RBAC Forbidden: Role '{auth.role}' cannot perform '{action}' on resource '{resource}'",
        )


class ValidateRequest(BaseModel):
    code: str
    language: ScriptLanguage


class ExplainFixRequest(BaseModel):
    code: str
    language: ScriptLanguage
    error_message: Optional[str] = None
    execution_output: Optional[str] = None


@router.post("/generate", response_model=ScriptGenerationResult)
async def generate_script(
    payload: ScriptGenerationRequest,
    auth: CurrentAuth,
) -> ScriptGenerationResult:
    """
    Synthesize an enterprise script (PowerShell, Bash, Python, SQL, Ansible)
    from natural language with embedded safety guardrails and error handling.
    """
    enforce_rbac(auth, "workflow", "create")
    try:
        return ai_scripting_engine.generate_script(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script synthesis error: {str(e)}")


@router.post("/validate", response_model=ScriptValidationResult)
async def validate_script(
    payload: ValidateRequest,
    auth: CurrentAuth,
) -> ScriptValidationResult:
    """
    Statically analyzes script for security vulnerabilities, destructive patterns, and syntax risks.
    """
    enforce_rbac(auth, "workflow", "read")
    try:
        return ai_scripting_engine.validate_script_safety(payload.code, payload.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script validation error: {str(e)}")


@router.post("/explain-fix", response_model=ScriptExplanationResult)
async def explain_and_fix_script(
    payload: ExplainFixRequest,
    auth: CurrentAuth,
) -> ScriptExplanationResult:
    """
    Generates a line-by-line explanation of a script and proposes automated fixes
    if execution errors or exceptions occurred.
    """
    enforce_rbac(auth, "workflow", "read")
    try:
        return ai_scripting_engine.explain_and_fix_script(
            code=payload.code,
            language=payload.language,
            error_message=payload.error_message,
            execution_output=payload.execution_output,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script explanation error: {str(e)}")
