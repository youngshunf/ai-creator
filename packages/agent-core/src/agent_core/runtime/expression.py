"""
表达式求值器 - 安全求值 Graph 中的表达式
@author Ysf
"""

import re
from typing import Any, Dict, Optional

from simpleeval import EvalWithCompoundTypes, NameNotDefined

from .context import RuntimeContext


class DictWrapper:
    """将字典包装为支持属性访问的对象"""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getattr__(self, name: str) -> Any:
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        if name in self._data:
            value = self._data[name]
            if isinstance(value, dict):
                return DictWrapper(value)
            return value
        return None  # 返回 None 而不是抛出异常

    def __getitem__(self, key: str) -> Any:
        return self._data.get(key)


class ExpressionEvaluator:
    """
    表达式求值器

    支持安全求值 ${...} 表达式，可引用 inputs、state、runtime 变量。

    示例:
        - ${inputs.topic}
        - ${state.outline}
        - ${runtime.model_default}
        - ${len(state.content) > 100}
        - ${inputs.count * 2 + 1}
    """

    # 表达式正则：匹配 ${...}
    EXPR_PATTERN = re.compile(r"\$\{([^}]+)\}")

    def __init__(self, ctx: RuntimeContext):
        """
        初始化表达式求值器

        Args:
            ctx: 运行时上下文
        """
        self.ctx = ctx
        self._evaluator = self._create_evaluator()

    def _create_evaluator(self) -> EvalWithCompoundTypes:
        """
        创建 SimpleEval 实例，配置安全函数和变量
        """
        evaluator = EvalWithCompoundTypes()

        # 允许的安全函数
        evaluator.functions = {
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "min": min,
            "max": max,
            "sum": sum,
            "abs": abs,
            "round": round,
        }

        # 禁止导入和属性访问（安全性）
        evaluator.names = {}

        return evaluator

    def evaluate(
        self,
        expr: str,
        inputs: Optional[Dict[str, Any]] = None,
        state: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        求值单个表达式

        Args:
            expr: 表达式字符串（可包含或不包含 ${...}）
            inputs: Graph 输入参数（可选，默认使用 ctx.inputs）
            state: Graph 状态变量（可选）

        Returns:
            求值结果

        Raises:
            ExpressionError: 表达式求值失败
        """
        # 使用传入的 inputs 或上下文中的 inputs
        inputs = inputs if inputs is not None else self.ctx.inputs
        state = state if state is not None else {}

        # 如果不是字符串，直接返回
        if not isinstance(expr, str):
            return expr

        # 如果不包含 ${...}，直接返回原字符串
        if "${" not in expr:
            return expr

        # 提取表达式内容（去掉 ${...}）
        match = self.EXPR_PATTERN.fullmatch(expr)
        if match:
            # 整个字符串是一个表达式
            expr_content = match.group(1).strip()
            return self._eval_expression(expr_content, inputs, state)
        else:
            # 字符串中包含多个表达式，需要替换
            return self._eval_template(expr, inputs, state)

    def _eval_expression(
        self, expr: str, inputs: Dict[str, Any], state: Dict[str, Any]
    ) -> Any:
        """
        求值单个表达式内容（已去除 ${...}）

        Args:
            expr: 表达式内容
            inputs: 输入参数
            state: 状态变量

        Returns:
            求值结果
        """
        # 构建变量上下文（使用 DictWrapper 支持属性访问）
        names = {
            "inputs": DictWrapper(inputs),
            "state": DictWrapper(state),
            "runtime": DictWrapper(self._create_runtime_namespace()),
        }

        # 使用 SimpleEval 安全求值
        self._evaluator.names = names
        try:
            return self._evaluator.eval(expr)
        except NameNotDefined as e:
            raise ExpressionError(
                f"表达式中引用了未定义的变量: {e}"
            ) from e
        except Exception as e:
            raise ExpressionError(
                f"表达式求值失败: {expr}, 错误: {e}"
            ) from e

    def _eval_template(
        self, template: str, inputs: Dict[str, Any], state: Dict[str, Any]
    ) -> str:
        """
        求值模板字符串（包含多个 ${...}）

        Args:
            template: 模板字符串
            inputs: 输入参数
            state: 状态变量

        Returns:
            替换后的字符串
        """

        def replacer(match):
            expr = match.group(1).strip()
            result = self._eval_expression(expr, inputs, state)
            return str(result)

        return self.EXPR_PATTERN.sub(replacer, template)

    def _create_runtime_namespace(self) -> Dict[str, Any]:
        """
        创建 runtime 命名空间

        Returns:
            包含 runtime 字段的字典
        """
        return {
            "user_id": self.ctx.user_id,
            "runtime_type": self.ctx.runtime_type.value,
            "model_default": self.ctx.model_default,
            "model_fast": self.ctx.model_fast,
            "trace_id": self.ctx.trace_id,
            "run_id": self.ctx.run_id,
            "device_type": self.ctx.device_type,
        }

    def evaluate_params(
        self,
        params: Dict[str, Any],
        inputs: Optional[Dict[str, Any]] = None,
        state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        批量求值参数字典

        递归处理嵌套的字典和列表，求值所有字符串表达式。

        Args:
            params: 参数字典
            inputs: 输入参数
            state: 状态变量

        Returns:
            求值后的参数字典
        """
        result = {}
        for key, value in params.items():
            result[key] = self._evaluate_value(value, inputs, state)
        return result

    def _evaluate_value(
        self,
        value: Any,
        inputs: Optional[Dict[str, Any]],
        state: Optional[Dict[str, Any]],
    ) -> Any:
        """
        递归求值单个值

        Args:
            value: 待求值的值
            inputs: 输入参数
            state: 状态变量

        Returns:
            求值后的值
        """
        if isinstance(value, str):
            # 字符串：尝试求值表达式
            return self.evaluate(value, inputs, state)
        elif isinstance(value, dict):
            # 字典：递归求值每个键值对
            return {
                k: self._evaluate_value(v, inputs, state)
                for k, v in value.items()
            }
        elif isinstance(value, list):
            # 列表：递归求值每个元素
            return [
                self._evaluate_value(item, inputs, state) for item in value
            ]
        else:
            # 其他类型：直接返回
            return value


class ExpressionError(Exception):
    """表达式求值错误"""

    pass
