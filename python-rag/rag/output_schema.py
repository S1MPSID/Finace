"""
Structured output schema for compliance analysis.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["HIGH", "MEDIUM", "LOW"]
CallType = Literal["general_query", "new_report", "update_report"]


class ApplicableClause(BaseModel):
    title: str = Field(default="")
    text: str = Field(default="")
    source: str = Field(default="")
    basis: str = Field(default="direct")
    applicability_note: str = Field(default="")


class ComplianceOutput(BaseModel):
    call_type: CallType = Field(default="general_query")
    risk_level: RiskLevel = Field(default="LOW")
    risk_flags: list[str] = Field(default_factory=list)
    applicable_clauses: list[ApplicableClause] = Field(default_factory=list)
    explanation: str = Field(default="")
    recommendations: list[str] = Field(default_factory=list)
    compliance_score: int = Field(default=80, ge=0, le=100)
    reasoning_steps: list[str] = Field(default_factory=list)
    superseded_references: list[str] = Field(default_factory=list)
    superseded_change_notes: list[str] = Field(default_factory=list)
