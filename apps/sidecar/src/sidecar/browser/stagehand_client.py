"""
Stagehand 客户端封装 - 集成 CreatorFlow LLM 网关

提供 Stagehand AI 浏览器自动化能力，使用云端 LiteLLM 网关。

@author Ysf
@date 2026-01-10
"""

import logging
from typing import Type, TypeVar, Optional, Any, Dict
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class StagehandClient:
    """
    Stagehand 客户端封装
    
    集成 CreatorFlow 云端 LLM 网关，提供 AI 驱动的浏览器自动化能力。
    
    注意：Stagehand 需要 LLM Token（CreatorFlow 平台登录后获取）才能工作，
    这与平台凭证（如小红书 cookies）是不同的认证。
    """
    
    @staticmethod
    def is_available() -> bool:
        """
        检查 Stagehand 是否可用
        
        需要同时满足：
        1. stagehand 包已安装
        2. 用户已登录 CreatorFlow（有 LLM API Token）
        
        Returns:
            bool: True 表示可用
        """
        # 检查 stagehand 是否安装
        try:
            import stagehand
        except ImportError:
            return False
        
        # 检查 LLM Token 是否存在
        try:
            from agent_core.llm.config import LLMConfigManager
            config_manager = LLMConfigManager()
            llm_config = config_manager.load()
            return bool(llm_config.api_token)
        except Exception:
            return False
    
    def __init__(self, headless: bool = True):
        """
        初始化 Stagehand 客户端
        
        Args:
            headless: 是否无头模式
        """
        self._headless = headless
        self._stagehand = None
        self._initialized = False
    
    async def _get_config(self):
        """
        获取 Stagehand 配置，使用 CreatorFlow LLM 网关
        
        使用 CloudLLMClient 动态获取模型，保持与系统其他部分一致。
        
        Returns:
            StagehandConfig: Stagehand 配置
        """
        try:
            from stagehand import StagehandConfig
        except ImportError:
            raise RuntimeError("stagehand 未安装，请运行: pip install stagehand")
        
        from agent_core.llm.config import LLMConfigManager
        from agent_core.llm.cloud_client import CloudLLMClient
        from agent_core.llm.interface import ModelType
        
        # 加载现有 LLM 配置
        config_manager = LLMConfigManager()
        llm_config = config_manager.load()
        
        if not llm_config.api_token:
            raise RuntimeError(
                "Stagehand 需要 LLM Token 才能工作。"
                "请先登录 CreatorFlow 平台获取 API Token。"
                "（注意：这与平台凭证如小红书 cookies 是不同的认证）"
            )
        
        # 使用 CloudLLMClient 动态获取模型（与系统其他部分保持一致）
        cloud_client = CloudLLMClient(llm_config)
        try:
            model_info = await cloud_client.get_model_by_type(ModelType.TEXT)
            model_name = model_info.model_id if model_info else llm_config.default_model
            logger.info(f"[StagehandClient] 从云端获取模型: {model_name}")
        except Exception as e:
            logger.warning(f"[StagehandClient] 获取动态模型失败，使用默认: {e}")
            model_name = llm_config.default_model
        finally:
            await cloud_client.close()
        
        # 构建 LLM 网关 URL (OpenAI 兼容格式)
        base_url = f"{llm_config.base_url}/api/v1/llm/proxy/v1"
        
        # 构建认证头
        headers = {}
        if llm_config.access_token:
            headers["Authorization"] = f"Bearer {llm_config.access_token}"
        
        logger.info(f"[StagehandClient] 配置 LLM 网关: {base_url}")
        logger.info(f"[StagehandClient] 使用模型: {model_name}")
        
        return StagehandConfig(
            env="LOCAL",  # 使用本地浏览器
            headless=self._headless,
            model_name=model_name,
            model_client_options={
                "base_url": base_url,
                "api_key": llm_config.api_token,
                "default_headers": headers,
            },
        )
    
    async def initialize(self):
        """初始化 Stagehand 实例"""
        if self._initialized:
            return
        
        try:
            from stagehand import Stagehand
        except ImportError:
            raise RuntimeError("stagehand 未安装，请运行: pip install stagehand")
        
        config = await self._get_config()
        self._stagehand = Stagehand(config)
        await self._stagehand.init()
        self._initialized = True
        
        logger.info("[StagehandClient] Stagehand 初始化完成")
    
    @property
    def page(self):
        """获取 Stagehand 页面对象"""
        if not self._initialized:
            raise RuntimeError("Stagehand 未初始化，请先调用 initialize()")
        return self._stagehand.page
    
    async def goto(self, url: str, **kwargs):
        """
        导航到指定 URL
        
        Args:
            url: 目标 URL
            **kwargs: 传递给 page.goto 的额外参数
        """
        await self.initialize()
        await self._stagehand.page.goto(url, **kwargs)
        logger.info(f"[StagehandClient] 导航到: {url}")
    
    async def act(self, instruction: str) -> None:
        """
        执行单个操作
        
        Args:
            instruction: 自然语言指令，如 "点击登录按钮"
        """
        await self.initialize()
        logger.info(f"[StagehandClient] 执行操作: {instruction}")
        await self._stagehand.page.act(instruction)
    
    async def extract(
        self, 
        instruction: str, 
        schema: Type[T],
    ) -> T:
        """
        结构化数据提取
        
        Args:
            instruction: 提取指令，如 "提取用户名和头像"
            schema: Pydantic 模型类
            
        Returns:
            T: 提取的结构化数据
        """
        await self.initialize()
        logger.info(f"[StagehandClient] 提取数据: {instruction}")
        result = await self._stagehand.page.extract(instruction, schema=schema)
        logger.info(f"[StagehandClient] 提取结果: {result}")
        return result
    
    async def observe(self, instruction: str) -> list:
        """
        观察页面，发现可操作元素
        
        Args:
            instruction: 观察指令，如 "找到发布按钮"
            
        Returns:
            list: 发现的元素列表
        """
        await self.initialize()
        logger.info(f"[StagehandClient] 观察页面: {instruction}")
        result = await self._stagehand.page.observe(instruction)
        return result
    
    async def agent_execute(self, task: str) -> str:
        """
        执行多步骤自主任务
        
        Args:
            task: 任务描述，如 "登录小红书并发布一篇笔记"
            
        Returns:
            str: 执行结果
        """
        await self.initialize()
        logger.info(f"[StagehandClient] Agent 执行: {task}")
        agent = self._stagehand.agent
        result = await agent.execute(task)
        logger.info(f"[StagehandClient] Agent 结果: {result}")
        return result
    
    async def add_cookies(self, cookies: list):
        """
        添加 Cookies
        
        Args:
            cookies: Cookie 列表
        """
        await self.initialize()
        context = self._stagehand.context
        await context.add_cookies(cookies)
        logger.info(f"[StagehandClient] 添加了 {len(cookies)} 个 cookies")
    
    async def get_cookies(self) -> list:
        """
        获取当前 Cookies
        
        Returns:
            list: Cookie 列表
        """
        await self.initialize()
        context = self._stagehand.context
        return await context.cookies()
    
    async def close(self):
        """关闭 Stagehand 实例"""
        if self._stagehand:
            await self._stagehand.close()
            self._stagehand = None
            self._initialized = False
            logger.info("[StagehandClient] Stagehand 已关闭")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
