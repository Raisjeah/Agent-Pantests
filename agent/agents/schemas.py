from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class Finding(BaseModel):
    type: str
    value: str
    evidence: str
    severity: Optional[str] = "info"

class LLMResponse(BaseModel):
    action_type: str = "analysis"
    confidence: float
    reasoning: str
    findings: List[Finding] = []
    status: str
    commands: Optional[List[str]] = []
