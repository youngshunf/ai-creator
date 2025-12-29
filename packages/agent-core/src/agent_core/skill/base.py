from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SkillMetadata(BaseModel):
    name: str = Field(..., description="技能名称")
    version: str = Field(..., description="技能版本")
    description: str = Field(..., description="技能描述")
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class SkillToolCall(BaseModel):
    name: str
    params: Dict[str, Any]

class SkillExampleTrace(BaseModel):
    thought: str
    tool_call: Optional[SkillToolCall] = None

class SkillExample(BaseModel):
    user: str
    assistant: SkillExampleTrace

class SkillSpec(BaseModel):
    tools: List[str] = Field(default_factory=list, description="依赖的工具名称列表")
    instructions: str = Field(..., description="注入给 LLM 的专家指令")
    examples: List[SkillExample] = Field(default_factory=list, description="Few-shot 示例")
    requirements: List[str] = Field(default_factory=list, description="依赖的 Python 包")

class Skill(BaseModel):
    apiVersion: str = "agent/v1"
    kind: str = "Skill"
    metadata: SkillMetadata
    spec: SkillSpec
