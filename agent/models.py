from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class PortInfo(BaseModel):
    port: str
    protocol: str
    state: str
    service: Optional[str] = ""
    product: Optional[str] = ""
    version: Optional[str] = ""

class Vulnerability(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    severity: str # info, low, medium, high, critical
    tool: str
    evidence_id: str
    metadata: Dict[str, Any] = {}

class Service(BaseModel):
    name: str
    version: Optional[str] = None
    port: Optional[str] = None
    protocol: Optional[str] = None

class ToolOutput(BaseModel):
    tool: str
    target: str
    status: str
    timestamp: str
    raw_output: str
    parsed_output: Dict[str, Any]
    errors: List[str] = []

class SecurityFinding(BaseModel):
    type: str # host, port, service, vulnerability, etc.
    value: str
    evidence: str
    severity: Optional[str] = "info"
    metadata: Dict[str, Any] = {}

class NormalizedState(BaseModel):
    target: str
    timestamp: datetime = Field(default_factory=datetime.now)
    ports: List[PortInfo] = []
    services: List[Service] = []
    vulnerabilities: List[Vulnerability] = []
    findings: List[SecurityFinding] = []
    errors: List[str] = []
