"""
工具注册表 - 管理工具注册和查找
@author Ysf
"""

from typing import Dict, Type, Optional, List
from .base import ToolInterface
from ..runtime.interfaces import RuntimeType


class ToolRegistry:
    """
    工具注册表

    支持两种使用模式：
    1. 类级别装饰器模式：使用 @ToolRegistry.register() 装饰器注册工具类
    2. 实例级别模式：创建 ToolRegistry 实例并使用 register_tool() 注册工具实例

    示例（装饰器模式）:
        @ToolRegistry.register("my_tool")
        class MyTool(ToolInterface):
            pass

    示例（实例模式）:
        registry = ToolRegistry(RuntimeType.LOCAL)
        registry.register_tool(MyTool())
        tool = registry.get_tool("my_tool")
    """

    # 类级别工具类存储（用于装饰器模式）
    _tool_classes: Dict[str, Type[ToolInterface]] = {}

    def __init__(self, runtime_type: Optional[RuntimeType] = None):
        """
        初始化工具注册表实例

        Args:
            runtime_type: 运行时类型（LOCAL 或 CLOUD）
        """
        self.runtime_type = runtime_type
        # 实例级别工具实例存储
        self._tools: Dict[str, ToolInterface] = {}

    # ==================== 实例方法（新增） ====================

    def register_tool(self, tool: ToolInterface) -> None:
        """
        注册工具实例

        Args:
            tool: 工具实例（必须实现 ToolInterface）

        Raises:
            ValueError: 如果工具没有名称或已存在同名工具
        """
        name = tool.get_name()
        if not name:
            raise ValueError("工具必须有有效的名称")

        # 检查运行时兼容性
        if self.runtime_type and hasattr(tool, 'metadata'):
            if self.runtime_type not in tool.metadata.supported_runtimes:
                raise ValueError(
                    f"工具 {name} 不支持运行时 {self.runtime_type.value}"
                )

        self._tools[name] = tool

    def get_tool(self, name: str) -> Optional[ToolInterface]:
        """
        获取工具实例

        Args:
            name: 工具名称

        Returns:
            工具实例，如果不存在则返回 None
        """
        return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        """
        检查工具是否已注册

        Args:
            name: 工具名称

        Returns:
            True 表示已注册，False 表示未注册
        """
        return name in self._tools

    def list_tools(self) -> List[str]:
        """
        列出所有已注册的工具名称

        Returns:
            工具名称列表
        """
        return list(self._tools.keys())

    def get_all_tools(self) -> Dict[str, ToolInterface]:
        """
        获取所有已注册的工具

        Returns:
            工具名称到工具实例的映射字典
        """
        return self._tools.copy()

    def unregister_tool(self, name: str) -> bool:
        """
        注销工具

        Args:
            name: 工具名称

        Returns:
            True 表示成功注销，False 表示工具不存在
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    # ==================== 类方法（保留兼容性） ====================

    @classmethod
    def register(cls, name: str, runtime_type: Optional[str] = None):
        """
        注册工具装饰器（类级别）

        用于装饰工具类，将其注册到全局注册表中。

        Args:
            name: 工具名称
            runtime_type: 运行时类型（可选）

        Returns:
            装饰器函数

        示例:
            @ToolRegistry.register("my_tool")
            class MyTool(ToolInterface):
                pass
        """
        def decorator(tool_class: Type[ToolInterface]):
            key = f"{name}:{runtime_type}" if runtime_type else name
            cls._tool_classes[key] = tool_class
            return tool_class
        return decorator

    @classmethod
    def register_universal(cls, name: str):
        """
        注册端云通用工具（类级别装饰器）

        Args:
            name: 工具名称

        Returns:
            装饰器函数
        """
        return cls.register(name, runtime_type=None)

    @classmethod
    def get(cls, name: str, runtime_type: Optional[str] = None) -> Optional[Type[ToolInterface]]:
        """
        获取工具类（类级别）

        Args:
            name: 工具名称
            runtime_type: 运行时类型（可选）

        Returns:
            工具类，如果不存在则返回 None
        """
        # 先查找特定运行时的工具
        if runtime_type:
            key = f"{name}:{runtime_type}"
            if key in cls._tool_classes:
                return cls._tool_classes[key]

        # 回退到通用工具
        return cls._tool_classes.get(name)

    @classmethod
    def get_all_classes(cls) -> Dict[str, Type[ToolInterface]]:
        """
        获取所有已注册的工具类（类级别）

        Returns:
            工具名称到工具类的映射字典
        """
        return cls._tool_classes.copy()

    @classmethod
    def list_registered_classes(cls) -> List[str]:
        """
        列出所有已注册的工具类名称（类级别）

        Returns:
            工具类名称列表
        """
        return list(cls._tool_classes.keys())
