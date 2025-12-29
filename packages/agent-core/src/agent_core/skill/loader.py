import os
import yaml
from typing import Dict, Optional, List, Any
from pathlib import Path

from .base import Skill

class SkillLoader:
    """负责加载 Skill 定义文件"""

    def __init__(self, skill_dirs: List[str] = None):
        self.skill_dirs = skill_dirs or []
        self._cache: Dict[str, Skill] = {}

    def load(self, skill_name: str) -> Skill:
        """加载指定名称的 Skill"""
        if skill_name in self._cache:
            return self._cache[skill_name]

        definition = self._load_from_file(skill_name)
        if not definition:
            raise FileNotFoundError(f"Skill '{skill_name}' not found in paths: {self.skill_dirs}")

        # Pydantic 验证
        skill = Skill(**definition)
        self._cache[skill_name] = skill
        return skill

    def _load_from_file(self, skill_name: str) -> Optional[Dict]:
        """从文件系统查找并加载 (.yaml/.yml/.md)"""
        # 优先查找 .md (Claude Friendly)
        extensions = ['.md', '.yaml', '.yml']
        
        for directory in self.skill_dirs:
            base_path = Path(directory)
            for ext in extensions:
                file_path = base_path / f"{skill_name}{ext}"
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        if ext == '.md':
                            return self._parse_markdown_skill(content)
                        else:
                            return yaml.safe_load(content)
                    except Exception as e:
                        raise ValueError(f"Failed to parse skill file {file_path}: {str(e)}")
        return None

    def _parse_markdown_skill(self, content: str) -> Dict[str, Any]:
        """
        解析 Markdown 格式的 Skill
        格式规范:
        ---
        name: xxx
        ...
        ---
        # Instructions
        ...
        """
        # 简单 Frontmatter 解析
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError("Invalid Markdown Skill format: missing Frontmatter delimiters (---)")
        
        # Part 0 is empty (before first ---)
        # Part 1 is YAML Frontmatter
        # Part 2 is Markdown Body
        
        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML Frontmatter: {str(e)}")
            
        body = parts[2].strip()
        
        # 构造符合 Skill Pydantic Model 的字典结构
        return {
            "apiVersion": "agent/v1",
            "kind": "Skill",
            "metadata": {
                "name": frontmatter.get("name"),
                "version": frontmatter.get("version"),
                "description": frontmatter.get("description"),
                "author": frontmatter.get("author"),
                "tags": frontmatter.get("tags", []),
            },
            "spec": {
                "tools": frontmatter.get("tools", []),
                "requirements": frontmatter.get("requirements", []),
                "instructions": body,
                "examples": [] # .md 模式下，示例隐含在 instructions 中
            }
        }

    def list_skills(self) -> List[str]:
        """列出所有可用 Skill 名称"""
        skills = set()
        extensions = ['.md', '.yaml', '.yml']
        
        for directory in self.skill_dirs:
            base_path = Path(directory)
            if not base_path.exists():
                continue
                
            for ext in extensions:
                for file_path in base_path.glob(f"*{ext}"):
                    skill_name = file_path.stem
                    skills.add(skill_name)
        return list(skills)
