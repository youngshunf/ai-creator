from typing import List, Dict, Any
from .base import Skill
from .loader import SkillLoader

class SkillManager:
    """Skill 管理器：负责管理和装配 Skill"""

    def __init__(self, skill_dirs: List[str]):
        self.loader = SkillLoader(skill_dirs)

    def load_skill(self, skill_name: str) -> Skill:
        return self.loader.load(skill_name)

    def equip_agent(self, context: Any, skill_names: List[str]) -> None:
        """
        为 Agent 装配技能
        
        Args:
            context: RuntimeContext (Duck Typing)
            skill_names: 技能名称列表
        """
        if not skill_names:
            return

        for name in skill_names:
            try:
                skill = self.load_skill(name)
                self._apply_skill(context, skill)
            except Exception as e:
                # 记录日志但为了健壮性暂不 crash? 或者应该 crash 暴露配置错误?
                # 这里选择抛出，因为配置错误应当尽早发现
                raise ValueError(f"Failed to equip skill '{name}': {str(e)}")

    def _apply_skill(self, context: Any, skill: Skill):
        """将 Skill 应用到 RuntimeContext"""
        
        # 1. 挂载工具 (假设 context.tools 是一个 List)
        # 注意: 这里的 tools 是 list string (tool names)，
        # 真正的 Tool 实例需要在 Executor/Runtime 层面根据 ToolRegistry 解析。
        # 这里我们将需要的工具名称添加进 context，供后续使用。
        if not hasattr(context, 'required_tools'):
             context.required_tools = []
        
        for tool_name in skill.spec.tools:
            if tool_name not in context.required_tools:
                context.required_tools.append(tool_name)

        # 2. 注入 Prompt
        # 假设 context.system_prompts 是一个 List[str]
        if not hasattr(context, 'system_prompts'):
            context.system_prompts = []
            
        skill_prompt = f"\n## Capability: {skill.metadata.name}\n{skill.spec.instructions}\n"
        context.system_prompts.append(skill_prompt)

        # 3. 注入 Examples (Few-Shot)
        # 假设 context.few_shot_examples 是一个 List[Dict]
        if not hasattr(context, 'few_shot_examples'):
            context.few_shot_examples = []
            
        for example in skill.spec.examples:
            # 转换为简单 dict 格式供 LLM 使用
            ex_dict = {
                "user": example.user,
                "assistant_thought": example.assistant.thought,
                "tool_call": example.assistant.tool_call.dict() if example.assistant.tool_call else None
            }
            context.few_shot_examples.append(ex_dict)
