"""
Sidecar 主入口 - JSON-RPC 服务

提供 Tauri 桌面端与 Python Sidecar 之间的通信接口。

@author Ysf
@date 2025-12-28
"""

import asyncio
import json
import sys
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

from agent_core.runtime.interfaces import ExecutionRequest
from agent_core.llm import LLMConfigManager, CloudLLMClient

from .executor import LocalExecutor


@dataclass
class JsonRpcRequest:
    """JSON-RPC 请求"""
    jsonrpc: str
    method: str
    params: Dict[str, Any]
    id: Optional[int] = None


@dataclass
class JsonRpcResponse:
    """JSON-RPC 响应"""
    jsonrpc: str = "2.0"
    result: Any = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[int] = None


class SidecarServer:
    """
    Sidecar JSON-RPC 服务器

    通过 stdin/stdout 与 Tauri 进行通信。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Sidecar 服务器

        Args:
            config: 配置字典
        """
        self.config = config
        self.executor: Optional[LocalExecutor] = None
        self.llm_client: Optional[CloudLLMClient] = None
        self._running = False

        # 方法映射
        self._methods = {
            "initialize": self._handle_initialize,
            "execute_graph": self._handle_execute_graph,
            "execute_graph_stream": self._handle_execute_graph_stream,
            "list_graphs": self._handle_list_graphs,
            "health_check": self._handle_health_check,
            "login": self._handle_login,
            "logout": self._handle_logout,
            "get_models": self._handle_get_models,
            "shutdown": self._handle_shutdown,
        }

    async def start(self):
        """启动服务器"""
        self._running = True

        # 初始化执行器
        await self._initialize_executor()

        # 主循环：读取 stdin，处理请求，写入 stdout
        while self._running:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                # 解析请求
                request = self._parse_request(line)
                if request is None:
                    continue

                # 处理请求
                response = await self._handle_request(request)

                # 发送响应
                self._send_response(response)

            except Exception as e:
                self._send_error(None, -32603, f"Internal error: {e}")

    async def _initialize_executor(self):
        """初始化执行器"""
        # 初始化 LLM 客户端
        llm_config_manager = LLMConfigManager()
        environment = self.config.get("environment", "production")
        llm_config = llm_config_manager.load(environment)

        if llm_config.api_token:
            self.llm_client = CloudLLMClient(llm_config)

        # 初始化执行器
        self.executor = LocalExecutor(self.config)

    def _parse_request(self, line: str) -> Optional[JsonRpcRequest]:
        """解析 JSON-RPC 请求"""
        try:
            data = json.loads(line)
            return JsonRpcRequest(
                jsonrpc=data.get("jsonrpc", "2.0"),
                method=data.get("method", ""),
                params=data.get("params", {}),
                id=data.get("id"),
            )
        except json.JSONDecodeError:
            self._send_error(None, -32700, "Parse error")
            return None

    async def _handle_request(self, request: JsonRpcRequest) -> JsonRpcResponse:
        """处理请求"""
        method = self._methods.get(request.method)
        if method is None:
            return JsonRpcResponse(
                error={"code": -32601, "message": f"Method not found: {request.method}"},
                id=request.id,
            )

        try:
            result = await method(request.params)
            return JsonRpcResponse(result=result, id=request.id)
        except Exception as e:
            return JsonRpcResponse(
                error={"code": -32603, "message": str(e)},
                id=request.id,
            )

    def _send_response(self, response: JsonRpcResponse):
        """发送响应"""
        data = {
            "jsonrpc": response.jsonrpc,
            "id": response.id,
        }
        if response.error:
            data["error"] = response.error
        else:
            data["result"] = response.result

        print(json.dumps(data), flush=True)

    def _send_error(self, request_id: Optional[int], code: int, message: str):
        """发送错误响应"""
        response = JsonRpcResponse(
            error={"code": code, "message": message},
            id=request_id,
        )
        self._send_response(response)

    # ==================== 请求处理方法 ====================

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """初始化"""
        return {
            "status": "ok",
            "version": "0.1.0",
            "capabilities": {
                "execute_graph": True,
                "execute_graph_stream": True,
                "browser_automation": True,
                "credential_store": True,
            },
        }

    async def _handle_execute_graph(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Graph"""
        import logging
        import traceback

        logger = logging.getLogger(__name__)

        if not self.executor:
            raise RuntimeError("Executor not initialized")

        logger.info(f"execute_graph params: {params}")

        request = ExecutionRequest(
            graph_name=params.get("graph_name", ""),
            inputs=params.get("inputs", {}),
            user_id=params.get("user_id", ""),
            session_id=params.get("session_id"),
            timeout=params.get("timeout", 300),
            trace_id=params.get("trace_id"),
        )

        try:
            response = await self.executor.execute(request)
            logger.info(f"execute_graph response: success={response.success}, error={response.error}")
        except Exception as e:
            logger.error(f"execute_graph exception: {e}")
            logger.error(traceback.format_exc())
            raise

        return {
            "success": response.success,
            "outputs": response.outputs,
            "error": response.error,
            "execution_id": response.execution_id,
            "trace_id": response.trace_id,
            "execution_time": response.execution_time,
        }

    async def _handle_execute_graph_stream(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """流式执行 Graph"""
        if not self.executor:
            raise RuntimeError("Executor not initialized")

        request = ExecutionRequest(
            graph_name=params.get("graph_name", ""),
            inputs=params.get("inputs", {}),
            user_id=params.get("user_id", ""),
            session_id=params.get("session_id"),
            timeout=params.get("timeout", 300),
            trace_id=params.get("trace_id"),
        )

        # 流式执行，逐个发送事件
        async for event in self.executor.execute_stream(request):
            # 发送事件通知
            event_data = {
                "jsonrpc": "2.0",
                "method": "event",
                "params": {
                    "type": event.type.value,
                    "data": event.data,
                },
            }
            print(json.dumps(event_data), flush=True)

        return {"status": "completed"}

    async def _handle_list_graphs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """列出可用的 Graph"""
        if not self.executor:
            raise RuntimeError("Executor not initialized")

        graphs = self.executor.graph_loader.list_graphs()
        return {"graphs": graphs}

    async def _handle_health_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """健康检查"""
        executor_healthy = False
        llm_healthy = False

        if self.executor:
            executor_healthy = await self.executor.health_check()

        if self.llm_client:
            llm_healthy = await self.llm_client.health_check()

        return {
            "healthy": executor_healthy,
            "executor": executor_healthy,
            "llm": llm_healthy,
        }

    async def _handle_login(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """用户登录"""
        api_token = params.get("api_token", "")
        access_token = params.get("access_token", "")
        access_token_expire_time = params.get("access_token_expire_time", "")
        refresh_token = params.get("refresh_token", "")
        refresh_token_expire_time = params.get("refresh_token_expire_time", "")
        environment = params.get("environment", "production")

        if not api_token:
            raise ValueError("api_token is required")

        # 保存 Token
        config_manager = LLMConfigManager()
        config_manager.save_token(
            api_token,
            environment,
            access_token,
            access_token_expire_time,
            refresh_token,
            refresh_token_expire_time,
        )

        # 重新初始化 LLM 客户端
        llm_config = config_manager.load(environment)
        self.llm_client = CloudLLMClient(llm_config)

        return {"status": "ok"}

    async def _handle_logout(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """用户登出"""
        environment = params.get("environment", "production")

        # 清除 Token
        config_manager = LLMConfigManager()
        config_manager.clear_token(environment)

        # 关闭 LLM 客户端
        if self.llm_client:
            await self.llm_client.close()
            self.llm_client = None

        return {"status": "ok"}

    async def _handle_get_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取可用模型列表"""
        if not self.llm_client:
            return {"models": []}

        models = await self.llm_client.get_available_models()
        return {
            "models": [
                {
                    "model_id": m.model_id,
                    "provider": m.provider.value,
                    "display_name": m.display_name,
                    "max_tokens": m.max_tokens,
                    "supports_streaming": m.supports_streaming,
                    "supports_vision": m.supports_vision,
                }
                for m in models
            ]
        }

    async def _handle_shutdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """关闭服务器"""
        self._running = False

        if self.executor:
            await self.executor.shutdown()

        if self.llm_client:
            await self.llm_client.close()

        return {"status": "ok"}


def main():
    """主函数"""
    import os
    import logging

    # 配置日志输出到 stderr
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        stream=sys.stderr,
    )

    # 从环境变量或默认值获取配置
    config = {
        "definitions_path": os.environ.get(
            "AGENT_DEFINITIONS_PATH", "agent-definitions"
        ),
        "environment": os.environ.get("AI_CREATOR_ENV", "development"),
        "api_keys": {},
    }

    # 创建并启动服务器
    server = SidecarServer(config)
    asyncio.run(server.start())


if __name__ == "__main__":
    main()
