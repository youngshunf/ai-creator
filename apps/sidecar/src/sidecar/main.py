"""
Sidecar 主入口 - JSON-RPC 服务

提供 Tauri 桌面端与 Python Sidecar 之间的通信接口。

@author Ysf
@date 2025-12-28
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

from agent_core.runtime.interfaces import ExecutionRequest
from agent_core.llm import LLMConfigManager, CloudLLMClient

from .executor import LocalExecutor
from .browser.manager import BrowserSessionManager
from .publish_executor import PublishExecutor
from .services.credential_sync import CredentialSyncClient
from .services.profile_sync import ProfileSyncClient
from .scheduler import get_sync_scheduler

logger = logging.getLogger(__name__)


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
        
        # 浏览器与发布服务
        self.browser_manager = BrowserSessionManager(headless=True)
        self.publish_executor = PublishExecutor(self.browser_manager)
        
        # 凭证同步服务
        self.credential_client: Optional[CredentialSyncClient] = None
        
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
            "sync_auth_tokens": self._handle_sync_auth_tokens,
            "shutdown": self._handle_shutdown,
            # 平台相关
            "get_platforms": self._handle_get_platforms,
            "adapt_content": self._handle_adapt_content,
            # 账号管理
            "start_platform_login": self._handle_start_platform_login,
            "check_login_status": self._handle_check_login_status,
            "close_login_browser": self._handle_close_login_browser,
            # 发布管理
            "publish_content": self._handle_publish_content,
            # 账号同步
            "sync_account": self._handle_sync_account,
            "sync_all_accounts": self._handle_sync_all_accounts,
            # 凭证同步
            "init_credential_sync": self._handle_init_credential_sync,
            "sync_credential": self._handle_sync_credential,
            "sync_all_credentials": self._handle_sync_all_credentials,
            "pull_credential": self._handle_pull_credential,
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
            extra={"access_token": params.get("access_token")},  # Pass access_token in extra
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

    async def _handle_sync_auth_tokens(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步前端登录的 Token 到本地配置
        
        前端通过 Axios 登录后，调用此方法将 Token 保存到本地，
        供 Sidecar 的 LLM 客户端使用。
        """
        import logging
        logger = logging.getLogger(__name__)
        
        api_token = params.get("api_token", "")
        access_token = params.get("access_token", "")
        access_token_expire_time = params.get("access_token_expire_time", "")
        refresh_token = params.get("refresh_token", "")
        refresh_token_expire_time = params.get("refresh_token_expire_time", "")
        environment = params.get("environment", "production")

        if not access_token:
            raise ValueError("access_token is required")

        logger.info(f"Syncing auth tokens (api_token={bool(api_token)}, access_token={bool(access_token)}, env={environment})")

        # 保存 Token 到本地配置文件
        config_manager = LLMConfigManager()
        config_manager.save_token(
            api_token,
            environment,
            access_token,
            access_token_expire_time,
            refresh_token,
            refresh_token_expire_time,
        )

        # 重新初始化 LLM 客户端 (使用新的 Token)
        llm_config = config_manager.load(environment)
        if self.llm_client:
            await self.llm_client.close()
        self.llm_client = CloudLLMClient(llm_config)
        
        logger.info("Auth tokens synced successfully, LLM client reinitialized")

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

    # ==================== 平台相关方法 ====================

    async def _handle_get_platforms(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取支持的平台列表"""
        from .platforms import PLATFORM_ADAPTERS, get_adapter

        platforms = []
        for name in PLATFORM_ADAPTERS:
            adapter = get_adapter(name)
            platforms.append({
                "name": adapter.platform_name,
                "display_name": adapter.platform_display_name,
                "login_url": adapter.login_url,
                "spec": {
                    "title_max_length": adapter.spec.title_max_length,
                    "content_max_length": adapter.spec.content_max_length,
                    "image_max_count": adapter.spec.image_max_count,
                    "video_max_count": adapter.spec.video_max_count,
                    "supported_formats": adapter.spec.supported_formats,
                },
            })
        return {"platforms": platforms}

    async def _handle_adapt_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配内容到指定平台"""
        from .platforms import get_adapter

        platform = params.get("platform", "")
        title = params.get("title", "")
        content = params.get("content", "")
        images = params.get("images", [])
        hashtags = params.get("hashtags", [])

        adapter = get_adapter(platform)
        adapted = adapter.adapt_content(title, content, images=images, hashtags=hashtags)

        return {
            "title": adapted.title,
            "content": adapted.content,
            "images": adapted.images,
            "hashtags": adapted.hashtags,
            "warnings": adapted.warnings,
        }

    # ==================== 账号管理方法 ====================

    async def _handle_start_platform_login(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """启动平台扫码登录 - 打开全新浏览器让用户登录"""
        from .platforms import get_adapter
        # BrowserSessionManager 已在 init 中导入，但这里可能需要局部导入或使用 self.browser_manager
        # 注意：这里我们是创建一个*新的*非无头浏览器用于登录，而不是使用 self.browser_manager (它是 headless 的)
        # 所以我们需要 BrowserSessionManager 类
        from .browser.manager import BrowserSessionManager

        platform = params.get("platform", "")
        # 使用临时 session_id 跟踪登录过程（不是最终的 account_id）
        session_id = f"login-{platform}-{int(asyncio.get_event_loop().time() * 1000)}"

        logger.info(f"[LOGIN] 启动登录: platform={platform}, session_id={session_id}")

        adapter = get_adapter(platform)

        # 每次添加新账号都创建新的浏览器管理器，确保是全新的浏览器
        if not hasattr(self, '_login_browser_manager'):
            self._login_browser_manager = {}

        # 创建全新的浏览器会话管理器（非无头模式）
        browser_manager = BrowserSessionManager(headless=False)
        self._login_browser_manager[session_id] = browser_manager

        try:
            # 获取全新的浏览器会话，不加载任何已保存的凭证
            logger.info(f"[LOGIN] 创建全新浏览器会话...")
            session = await browser_manager.get_session(
                platform=platform,
                account_id=session_id,
                load_credentials=False,  # 关键：不加载任何已保存的凭证
            )

            # 导航到登录页面
            logger.info(f"[LOGIN] 导航到登录页面: {adapter.login_url}")
            await session.page.goto(adapter.login_url, wait_until="domcontentloaded")

            logger.info(f"[LOGIN] 浏览器已打开, session_id={session_id}")

            return {
                "status": "browser_opened",
                "platform": platform,
                "account_id": session_id,  # 返回临时 session_id，用于后续轮询
                "login_url": adapter.login_url,
                "message": f"浏览器已打开，请在浏览器中完成 {adapter.platform_display_name} 登录",
            }

        except Exception as e:
            logger.error(f"[LOGIN] 启动浏览器失败: {e}")
            return {
                "status": "error",
                "platform": platform,
                "error": str(e),
                "message": f"启动浏览器失败: {e}",
            }

    async def _handle_check_login_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """检查平台登录状态并保存凭证"""
        from .platforms import get_adapter

        platform = params.get("platform", "")
        session_id = params.get("account_id", "")

        logger.info(f"[LOGIN] 检查登录状态: platform={platform}, session_id={session_id}")

        if not hasattr(self, '_login_browser_manager') or session_id not in self._login_browser_manager:
            return {"status": "error", "logged_in": False, "message": "登录会话不存在"}

        browser_manager = self._login_browser_manager[session_id]
        session_key = f"{platform}:{session_id}"

        if session_key not in browser_manager._sessions:
            return {"status": "error", "logged_in": False, "message": "浏览器会话不存在"}

        session = browser_manager._sessions[session_key]

        try:
            page = session.page
            current_url = page.url

            # 获取 cookies 和 localStorage
            cookies = await page.context.cookies()
            local_storage_str = await page.evaluate("() => JSON.stringify(localStorage)")
            storage_data = json.loads(local_storage_str) if local_storage_str != '{}' else {}

            # 使用适配器检查登录状态
            adapter = get_adapter(platform)
            login_result = await adapter.check_login_status(cookies, storage_data, current_url)

            if login_result.is_logged_in:
                platform_user_id = login_result.platform_user_id
                if not platform_user_id:
                    return {"status": "error", "logged_in": False, "message": "无法获取平台用户ID"}

                logger.info(f"[LOGIN] 登录成功，平台用户ID: {platform_user_id}")

                # 在登录成功时直接获取用户资料（避免单独同步时触发安全验证）
                account_info = await self._get_account_info(page, platform)
                logger.info(f"[LOGIN] 获取到用户资料: {account_info}")

                # 更新 session 并保存凭证
                session.account_id = platform_user_id
                browser_manager._sessions[f"{platform}:{platform_user_id}"] = session
                del browser_manager._sessions[session_key]
                await browser_manager.save_session_credentials(platform, platform_user_id)

                return {
                    "status": "success",
                    "logged_in": True,
                    "platform": platform,
                    "account_id": platform_user_id,
                    # 前端期望的字段名: account_name, avatar_url
                    "account_name": account_info.get("name", ""),
                    "avatar_url": account_info.get("avatar", ""),
                    "followers_count": account_info.get("followers_count", 0),
                    "message": "登录成功，凭证已保存",
                }
            else:
                return {"status": "pending", "logged_in": False, "message": "等待用户完成登录..."}

        except Exception as e:
            error_msg = str(e)
            # 处理页面导航导致的上下文丢失错误 (通常发生在重定向或页面刷新时)
            if "Execution context was destroyed" in error_msg or "Target closed" in error_msg:
                # 这是一个预期的竞态条件，不应视为错误，而是让前端继续轮询
                logger.warning(f"[LOGIN] 页面正在导航或刷新，上下文暂时不可用: {error_msg}")
                return {
                    "status": "pending", 
                    "logged_in": False, 
                    "message": "页面跳转中..."
                }

            logger.error(f"[LOGIN] 检查登录状态失败: {e}", exc_info=True)
            return {"status": "error", "logged_in": False, "error": str(e), "message": f"检查登录状态失败: {e}"}

    async def _handle_close_login_browser(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """关闭登录浏览器"""
        session_id = params.get("account_id", "")

        if hasattr(self, '_login_browser_manager') and session_id in self._login_browser_manager:
            browser_manager = self._login_browser_manager[session_id]
            await browser_manager.close()
            del self._login_browser_manager[session_id]

        return {"status": "closed", "message": "浏览器已关闭"}

    async def _check_platform_logged_in(self, page, platform: str) -> bool:
        """检查平台是否已登录 - 同时检测 cookie 和 localStorage"""
        try:
            # 获取 cookies
            cookies = await page.context.cookies()
            cookie_names = [c['name'] for c in cookies]

            # 获取 localStorage
            local_storage_str = await page.evaluate("() => JSON.stringify(localStorage)")
            storage_data = json.loads(local_storage_str) if local_storage_str != '{}' else {}
            logger.info(f"[LOGIN] cookies: {cookie_names[:10]}...")
            logger.info(f"[LOGIN] localStorage keys: {list(storage_data.keys())}")

            if platform == "xiaohongshu":
                # 小红书：必须离开登录页面且有用户信息
                current_url = page.url
                is_on_login_page = '/login' in current_url
                has_user_info = 'USER_INFO' in storage_data or 'USER_INFO_FOR_BIZ' in storage_data
                logged_in = not is_on_login_page and has_user_info
                logger.info(f"[LOGIN] 小红书登录检测: is_on_login_page={is_on_login_page}, has_user_info={has_user_info}")
                return logged_in
            elif platform == "douyin":
                login_cookies = ['sessionid', 'passport_csrf_token']
                return any(c in cookie_names for c in login_cookies)
            elif platform == "wechat":
                login_cookies = ['slave_sid', 'slave_user']
                return any(c in cookie_names for c in login_cookies)
            return False
        except Exception as e:
            logger.error(f"[LOGIN] 检测登录状态异常: {e}")
            return False

    async def _get_account_info(self, page, platform: str) -> Dict[str, str]:
        """获取账号信息 - 从 localStorage 或页面元素获取"""
        try:
            if platform == "xiaohongshu":
                # 优先从 localStorage 获取用户信息
                user_info_str = await page.evaluate("() => localStorage.getItem('USER_INFO_FOR_BIZ')")
                logger.info(f"[LOGIN] USER_INFO_FOR_BIZ 原始值: {user_info_str}")
                if user_info_str:
                    user_info = json.loads(user_info_str)
                    logger.info(f"[LOGIN] 解析后用户信息: {user_info}")
                    return {
                        "name": user_info.get("userName", ""),
                        "avatar": user_info.get("userAvatar", ""),
                        "user_id": user_info.get("userId", ""),
                    }
                # 备用：尝试 USER_INFO
                user_info_str = await page.evaluate("() => localStorage.getItem('USER_INFO')")
                logger.info(f"[LOGIN] USER_INFO 原始值: {user_info_str}")
                if user_info_str:
                    user_info = json.loads(user_info_str)
                    user_data = user_info.get("user", {}).get("value", {})
                    return {
                        "name": user_data.get("userId", ""),
                        "avatar": "",
                        "user_id": user_data.get("userId", ""),
                    }
                # 备用：从搜索历史键中提取用户ID
                local_storage_str = await page.evaluate("() => JSON.stringify(localStorage)")
                storage_data = json.loads(local_storage_str) if local_storage_str != '{}' else {}
                for key in storage_data.keys():
                    if key.startswith('xhs-pc-search-history-'):
                        user_id = key.replace('xhs-pc-search-history-', '')
                        logger.info(f"[LOGIN] 从搜索历史键提取用户ID: {user_id}")
                        return {
                            "name": f"小红书用户",
                            "avatar": "",
                            "user_id": user_id,
                        }
            elif platform == "douyin":
                name = await page.locator('[class*="user-name"], [class*="nickname"]').first.text_content() or ""
                avatar = await page.locator('[class*="avatar"] img').first.get_attribute("src") or ""
                return {"name": name.strip(), "avatar": avatar}
            elif platform == "wechat":
                name = await page.locator('[class*="weui-desktop-account__nickname"]').first.text_content() or ""
                avatar = await page.locator('[class*="weui-desktop-account__avatar"] img').first.get_attribute("src") or ""
                return {"name": name.strip(), "avatar": avatar}
        except Exception as e:
            logger.error(f"[LOGIN] 获取账号信息失败: {e}")
        return {"name": "", "avatar": ""}

    # ==================== 发布管理方法 ====================

    async def _handle_publish_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """发布内容到平台"""
        
        platform = params.get("platform", "")
        title = params.get("title", "")
        content = params.get("content", "")
        images = params.get("images", [])
        videos = params.get("videos", [])
        hashtags = params.get("hashtags", [])
        account_id = params.get("account_id", "")

        logger.info(f"[PUBLISH] 收到发布请求: platform={platform}, account={account_id}, title={title}")

        if not platform or not account_id:
            return {"success": False, "error": "缺少 platform 或 account_id"}

        # 构造发布内容字典
        publish_content = {
            "title": title,
            "content": content,
            "images": images,
            "videos": videos,
            "hashtags": hashtags,
        }

        # 执行发布
        try:
            result = await self.publish_executor.execute_publish(
                platform=platform,
                account_id=account_id,
                content=publish_content
            )

            return {
                "success": result.success,
                "post_url": result.platform_post_url,
                "post_id": result.platform_post_id,
                "error": result.error_message,
                "extra": result.extra,
            }
        except Exception as e:
            logger.exception(f"[PUBLISH] 发布请求处理异常: {e}")
            return {
                "success": False,
                "error": f"发布异常: {str(e)}"
            }

    # ==================== 账号同步方法 ====================

    async def _handle_sync_account(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """同步单个账号的用户资料"""
        from .scheduler import get_sync_scheduler

        platform = params.get("platform", "")
        account_id = params.get("account_id", "")

        if not platform or not account_id:
            return {"success": False, "error": "缺少 platform 或 account_id"}

        scheduler = get_sync_scheduler()
        result = await scheduler.sync_account(platform, account_id)

        return {
            "success": result.success,
            "platform": result.platform,
            "account_id": result.account_id,
            "profile": result.profile,
            "error": result.error,
        }

    async def _handle_sync_all_accounts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """同步所有账号"""
        from .scheduler import get_sync_scheduler

        scheduler = get_sync_scheduler()
        results = await scheduler.sync_all()

        return {
            "success": True,
            "total": len(results),
            "succeeded": sum(1 for r in results if r.success),
            "results": [
                {"platform": r.platform, "account_id": r.account_id, "success": r.success, "error": r.error}
                for r in results
            ],
        }


    # ==================== 凭证同步方法 ====================

    async def _handle_init_credential_sync(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """初始化凭证同步客户端"""
        api_base_url = params.get("api_base_url", "")
        auth_token = params.get("auth_token", "")
        master_key = params.get("master_key", "")
        
        if not api_base_url or not auth_token or not master_key:
            return {"success": False, "error": "Missing required parameters: api_base_url, auth_token, master_key"}
            
        try:
            self.credential_client = CredentialSyncClient(
                api_base_url=api_base_url,
                auth_token=auth_token,
                master_key=master_key
            )
            
            # 同时初始化资料同步客户端并设置给调度器
            profile_client = ProfileSyncClient(
                api_base_url=api_base_url,
                auth_token=auth_token
            )
            scheduler = get_sync_scheduler()
            scheduler.set_sync_client(profile_client)
            
            return {"success": True, "message": "Credential & Profile sync client initialized"}
        except Exception as e:
            logger.exception(f"[SYNC] Init credential client failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_sync_credential(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """同步单个凭证"""
        if not self.credential_client:
            return {"success": False, "error": "Credential sync client not initialized"}
            
        platform = params.get("platform", "")
        account_id = params.get("account_id", "")
        
        if not platform or not account_id:
             return {"success": False, "error": "Missing platform or account_id"}
             
        try:
            result = await self.credential_client.sync_credential(platform, account_id)
            return {
                "success": result.success,
                "version": result.version,
                "message": result.message
            }
        except Exception as e:
            logger.exception(f"[SYNC] Sync credential failed: {e}")
            return {"success": False, "error": str(e)}
        
    async def _handle_sync_all_credentials(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """同步所有凭证"""
        if not self.credential_client:
            return {"success": False, "error": "Credential sync client not initialized"}
            
        try:
            results = await self.credential_client.sync_all()
            return {
                "success": True,
                "results": [
                    {
                        "platform": r.platform,
                        "account_id": r.account_id,
                        "success": r.success,
                        "message": r.message
                    } for r in results
                ]
            }
        except Exception as e:
             logger.exception(f"[SYNC] Sync all credentials failed: {e}")
             return {"success": False, "error": str(e)}

    async def _handle_pull_credential(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """拉取凭证"""
        if not self.credential_client:
            return {"success": False, "error": "Credential sync client not initialized"}
            
        platform = params.get("platform", "")
        account_id = params.get("account_id", "")
        
        if not platform or not account_id:
             return {"success": False, "error": "Missing platform or account_id"}
             
        try:
            result = await self.credential_client.pull_credential(platform, account_id)
            return {
                "success": result.success,
                "version": result.version,
                "message": result.message
            }
        except Exception as e:
             logger.exception(f"[SYNC] Pull credential failed: {e}")
             return {"success": False, "error": str(e)}


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
