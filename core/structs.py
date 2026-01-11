from pydantic import BaseModel, Field
from typing import List, Optional

class TargetConfig(BaseModel):
    in_scope_domains: List[str] = Field(default_factory=list, description="List of domains that are safe to attack")
    out_of_scope_domains: List[str] = Field(default_factory=list, description="List of domains that are strictly forbidden")
    excluded_vulnerabilities: List[str] = Field(default_factory=list, description="Vulnerability types to ignore")

class ScanResult(BaseModel):
    domain: str
    vulnerabilities: List[dict] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)

class Vulnerability(BaseModel):
    title: str
    severity: str
    url: str
    description: str
    proof: Optional[str] = None
