# Stagehand 集成实施计划

> 版本: v1.0 | 日期: 2026-01-10

## 1. 目标

集成 Stagehand AI 浏览器自动化框架到 CreatorFlow 桌面端，实现：

- 静默账号同步（无弹窗）
- AI 驱动的作品发布
- 自愈能力应对平台 UI 变化

---

## 2. 设计概述

### 2.1 混合浏览器策略

```text
┌─────────────────────────────────────────────────────────────┐
│                  HybridBrowserManager                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  首次登录 ──────► CDP 真实浏览器 (最高反检测)                │
│  账号同步 ──────► Stagehand extract() (AI 提取)             │
│  作品发布 ──────► Stagehand agent() (多步骤任务)            │
│  Fallback ──────► Playwright + Stealth                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 LLM 网关集成

Stagehand 使用现有 CreatorFlow 云端 LiteLLM 网关：

- Base URL: `{llm_config.base_url}/api/v1/llm/proxy/v1`
- API Key: 用户登录后获取的 `api_token`
- 认证: JWT Bearer Token

---

## 3. 变更计划

### 3.1 依赖更新

#### [MODIFY] [pyproject.toml](file:///Users/mac/saas/ai-creator/apps/sidecar/pyproject.toml)

添加 stagehand 依赖：

```diff
 dependencies = [
     "agent-core",
     "playwright>=1.40.0",
     "apscheduler>=3.10.0",
     "cryptography>=41.0.0",
+    "stagehand>=0.1.0",
 ]
```

---

### 3.2 Stagehand 客户端封装

#### [NEW] [stagehand_client.py](file:///Users/mac/saas/ai-creator/apps/sidecar/src/sidecar/browser/stagehand_client.py)

创建 Stagehand 客户端封装，集成 LLM 网关：

```python
class StagehandClient:
    """Stagehand 客户端 - 集成 CreatorFlow LLM 网关"""

    async def create_config(self) -> StagehandConfig:
        """创建配置，使用云端 LLM 网关"""

    async def extract(self, instruction: str, schema: Type[BaseModel]) -> T:
        """结构化数据提取"""

    async def act(self, instruction: str) -> None:
        """执行单个操作"""

    async def agent_execute(self, task: str) -> str:
        """执行多步骤任务"""
```

---

### 3.3 账号同步服务重构

#### [MODIFY] [account_sync.py](file:///Users/mac/saas/ai-creator/apps/sidecar/src/sidecar/services/account_sync.py)

重构为使用 Stagehand：

```diff
 class AccountSyncService:
-    async def sync_account(self, platform: str, account_id: str) -> SyncResult:
-        browser_manager = BrowserSessionManager(headless=False)
+    async def sync_account(
+        self,
+        platform: str,
+        account_id: str,
+        use_stagehand: bool = True,
+    ) -> SyncResult:
+        if use_stagehand:
+            return await self._sync_with_stagehand(platform, account_id)
+        else:
+            return await self._sync_with_playwright(platform, account_id)
```

---

### 3.4 混合浏览器管理器

#### [NEW] [hybrid_manager.py](file:///Users/mac/saas/ai-creator/apps/sidecar/src/sidecar/browser/hybrid_manager.py)

```python
class HybridBrowserManager:
    """混合浏览器管理器 - 根据场景选择最佳方案"""

    async def login(self, platform: str, account_id: str):
        """首次登录 - 使用 CDP 真实浏览器"""

    async def sync_profile(self, platform: str, account_id: str) -> UserProfile:
        """账号同步 - 使用 Stagehand extract()"""

    async def publish(self, platform: str, content: dict):
        """发布内容 - 使用 Stagehand agent()"""
```

---

### 3.5 数据模型

#### [NEW] [schemas.py](file:///Users/mac/saas/ai-creator/apps/sidecar/src/sidecar/browser/schemas.py)

Pydantic Schema 用于 Stagehand 结构化提取：

```python
class UserProfile(BaseModel):
    nickname: str = Field(..., description="用户昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    followers: Optional[int] = Field(None, description="粉丝数")
    user_id: Optional[str] = Field(None, description="用户ID")
```

---

## 4. 验证计划

### 4.1 单元测试

| 测试项               | 文件                             | 命令                                                                 |
| -------------------- | -------------------------------- | -------------------------------------------------------------------- |
| Stagehand 客户端配置 | `tests/test_stagehand_client.py` | `cd apps/sidecar && uv run pytest tests/test_stagehand_client.py -v` |

### 4.2 集成测试

| 测试项       | 说明                                   |
| ------------ | -------------------------------------- |
| LLM 网关连接 | 验证 Stagehand 能正确调用云端 LLM 网关 |
| 账号同步     | 验证静默模式下的账号同步               |

### 4.3 手动测试

**测试步骤**:

1. 启动桌面端应用
2. 登录已有的平台账号（如小红书）
3. 触发账号同步功能
4. 验证：
   - 浏览器窗口不弹出
   - 账号信息正确同步
   - 无反爬虫检测错误

---

## 5. 文件清单

| 操作   | 文件路径                                               |
| ------ | ------------------------------------------------------ |
| MODIFY | `apps/sidecar/pyproject.toml`                          |
| NEW    | `apps/sidecar/src/sidecar/browser/stagehand_client.py` |
| NEW    | `apps/sidecar/src/sidecar/browser/hybrid_manager.py`   |
| NEW    | `apps/sidecar/src/sidecar/browser/schemas.py`          |
| MODIFY | `apps/sidecar/src/sidecar/services/account_sync.py`    |
| NEW    | `apps/sidecar/tests/test_stagehand_client.py`          |
