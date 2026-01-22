"""
平台适配器模块 - 兼容层

此模块现在从 agent_core.platforms 透传所有导出。
保留此文件是为了向后兼容现有的 sidecar 代码。

@author Ysf
@deprecated 请直接使用 agent_core.platforms
"""

import importlib.util
import sys
from pathlib import Path


def _load_module_directly(module_name: str, file_path: Path):
    """直接从文件加载模块，绕过包的 __init__.py"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# 找到 agent-core 的 platforms 目录
_this_file = Path(__file__).resolve()
_sidecar_src = _this_file.parent.parent.parent  # apps/sidecar/src
_agent_core_platforms = _sidecar_src.parent.parent.parent / "packages" / "agent-core" / "src" / "agent_core" / "platforms"

# 绕过 agent_core/__init__.py，直接加载子模块
if "agent_core.platforms.config" not in sys.modules:
    # 先加载依赖的 config 模块
    _config_init = _agent_core_platforms / "config" / "__init__.py"
    _config_schema = _agent_core_platforms / "config" / "schema.py"
    _config_loader = _agent_core_platforms / "config" / "loader.py"
    
    if _config_schema.exists():
        _load_module_directly("agent_core.platforms.config.schema", _config_schema)
    if _config_loader.exists():
        _load_module_directly("agent_core.platforms.config.loader", _config_loader)
    if _config_init.exists():
        _load_module_directly("agent_core.platforms.config", _config_init)

# 加载 models
_models_file = _agent_core_platforms / "models.py"
if _models_file.exists() and "agent_core.platforms.models" not in sys.modules:
    _models = _load_module_directly("agent_core.platforms.models", _models_file)
else:
    import agent_core.platforms.models as _models

# 加载 adapter 基类
_adapter_file = _agent_core_platforms / "adapter.py"
if _adapter_file.exists() and "agent_core.platforms.adapter" not in sys.modules:
    _adapter = _load_module_directly("agent_core.platforms.adapter", _adapter_file)
else:
    import agent_core.platforms.adapter as _adapter

# 加载 adapters 模块
_adapters_init = _agent_core_platforms / "adapters" / "__init__.py"
if _adapters_init.exists() and "agent_core.platforms.adapters" not in sys.modules:
    # 先加载各个适配器
    for adapter_name in ["xiaohongshu", "douyin", "bilibili", "wechat"]:
        adapter_file = _agent_core_platforms / "adapters" / f"{adapter_name}.py"
        if adapter_file.exists():
            _load_module_directly(f"agent_core.platforms.adapters.{adapter_name}", adapter_file)
    _adapters = _load_module_directly("agent_core.platforms.adapters", _adapters_init)
else:
    import agent_core.platforms.adapters as _adapters

# 导出
ContentSpec = _models.ContentSpec
AdaptedContent = _models.AdaptedContent
LoginResult = _models.LoginResult
UserProfile = _models.UserProfile
PublishResult = _models.PublishResult

PlatformAdapter = _adapter.PlatformAdapter

XiaohongshuAdapter = _adapters.XiaohongshuAdapter
WechatAdapter = _adapters.WechatAdapter
DouyinAdapter = _adapters.DouyinAdapter
BilibiliAdapter = _adapters.BilibiliAdapter
PLATFORM_ADAPTERS = _adapters.PLATFORM_ADAPTERS
get_adapter = _adapters.get_adapter
list_platforms = _adapters.list_platforms

# 向后兼容别名
ContentConstraints = ContentSpec

__all__ = [
    # 基类和模型
    "PlatformAdapter",
    "AdaptedContent",
    "ContentSpec",
    "ContentConstraints",  # 兼容别名
    "LoginResult",
    "UserProfile",
    "PublishResult",
    # 适配器
    "XiaohongshuAdapter",
    "WechatAdapter",
    "DouyinAdapter",
    "BilibiliAdapter",
    # 工具函数
    "get_adapter",
    "list_platforms",
    "PLATFORM_ADAPTERS",
]
