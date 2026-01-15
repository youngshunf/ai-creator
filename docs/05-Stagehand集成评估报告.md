# Stagehand 集成评估报告

> 评估日期: 2026-01-10 | 评估对象: [Stagehand](https://github.com/browserbase/stagehand)

## 1. Stagehand 概述

**Stagehand** 是由 Browserbase 开发的 **AI 浏览器自动化框架**，提供 TypeScript 和 Python SDK，通过自然语言控制浏览器，具有自愈能力。GitHub ⭐️ 18k+。

### 1.1 核心 API

| API         | 功能     | 说明                             |
| ----------- | -------- | -------------------------------- |
| `act()`     | 执行操作 | 自然语言描述，如 "点击登录按钮"  |
| `extract()` | 数据提取 | 结构化输出，支持 Pydantic Schema |
| `observe()` | 页面观察 | 发现可操作元素，返回选择器       |
| `agent()`   | 自主代理 | 执行多步骤复杂任务               |

### 1.2 关键特性

- **本地运行**: `env="LOCAL"` 无需 Browserbase 云服务，免费使用
- **自愈能力**: 自动适应平台 UI 变化，减少维护成本
- **动作缓存**: 缓存已执行的操作，避免重复 LLM 调用
- **结构化提取**: 使用 Pydantic Schema 确保数据类型正确

---

## 2. Python SDK 示例 (使用 CreatorFlow LLM 网关)

> [!IMPORTANT]
> Stagehand 支持 OpenAI 兼容 API，直接对接现有 CreatorFlow 云端 LiteLLM 网关

```python
# 安装: pip install stagehand
from stagehand import Stagehand, StagehandConfig
from pydantic import BaseModel, Field
from agent_core.llm.config import LLMConfigManager

class UserProfile(BaseModel):
    nickname: str = Field(..., description="用户昵称")
    avatar_url: str = Field(..., description="头像URL")
    followers: int = Field(..., description="粉丝数")

async def sync_account():
    # 🔥 从现有配置读取 Token (与 cloud_client.py 保持一致)
    config_manager = LLMConfigManager()
    llm_config = config_manager.load()

    # 🔥 配置 Stagehand 使用 CreatorFlow 云端 LLM 网关
    config = StagehandConfig(
        env="LOCAL",  # 本地浏览器，无需 Browserbase 云服务

        # 使用云端 LiteLLM 网关 (OpenAI 兼容格式)
        model_name=llm_config.default_model,  # 如 "claude-sonnet-4-5-20250929"
        model_client_options={
            "base_url": f"{llm_config.base_url}/api/v1/llm/proxy/v1",
            "api_key": llm_config.api_token,  # 用户的 API Token (sk-cf-xxx)
            "default_headers": {
                "Authorization": f"Bearer {llm_config.access_token}",  # JWT 认证
            },
        },
    )

    stagehand = Stagehand(config)
    await stagehand.init()

    # 导航到平台
    await stagehand.page.goto("https://creator.xiaohongshu.com")

    # 🔥 结构化数据提取 - 自动适应 UI 变化
    profile = await stagehand.page.extract(
        "提取用户名、头像URL、粉丝数",
        schema=UserProfile
    )

    await stagehand.close()
    return profile
```

### LLM 网关配置说明

| 配置项       | 值                                               | 说明                       |
| ------------ | ------------------------------------------------ | -------------------------- |
| `base_url`   | `https://api.ai-creator.com/api/v1/llm/proxy/v1` | 云端 LLM 网关              |
| `api_key`    | `sk-cf-xxx`                                      | 用户登录后获取的 API Token |
| `model_name` | `claude-sonnet-4-5-20250929`                     | 网关中配置的模型 ID        |

---

## 3. 方案全面对比

| 特性               |   **Stagehand**   | **CDP真实浏览器** | **browser-use** | **Playwright+Stealth** |
| ------------------ | :---------------: | :---------------: | :-------------: | :--------------------: |
| **自然语言操作**   |    ✅ 原生支持    |  ❌ 需要 AI 包装  |   ✅ 原生支持   |    ❌ 需要 AI 包装     |
| **自愈能力**       | ✅ 自适应 UI 变化 |       ❌ 无       |     ⚠️ 有限     |         ❌ 无          |
| **本地浏览器支持** | ✅ `env="LOCAL"`  |    ✅ 原生支持    |     ✅ 支持     |        ✅ 支持         |
| **反检测能力**     |     ⭐⭐⭐⭐      |    ⭐⭐⭐⭐⭐     |     ⭐⭐⭐      |         ⭐⭐⭐         |
| **静默运行**       | ✅ headless 支持  |   ✅ 最小化模式   |    ⚠️ 需配置    |       ⚠️ 需配置        |
| **结构化数据提取** |  ✅ Pydantic/Zod  |   ❌ 需手动实现   |     ⚠️ 有限     |     ❌ 需手动实现      |
| **无需选择器**     |  ✅ AI 理解页面   |   ❌ 需要选择器   | ✅ AI 理解页面  |     ❌ 需要选择器      |
| **动作缓存**       |    ✅ 内置支持    |     ⚠️ 需手动     |      ❌ 无      |         ❌ 无          |
| **LLM token 成本** |     ⚠️ 有消耗     |       ❌ 无       |    ⚠️ 有消耗    |         ❌ 无          |
| **社区活跃度**     |   ⭐ 18k stars    |         -         |  ⭐ 1.5k stars  |           -            |

---

## 4. Stagehand vs 当前 browser-use

| 维度         | 当前 browser-use  | Stagehand                   | 评估              |
| ------------ | ----------------- | --------------------------- | ----------------- |
| **API 设计** | 单一 `run()` 方法 | `act/extract/observe/agent` | ✅ Stagehand 更优 |
| **数据提取** | 靠 LLM 解析文本   | Pydantic Schema 验证        | ✅ Stagehand 更优 |
| **可靠性**   | 依赖 GPT-4o 理解  | 自愈 + 动作缓存             | ✅ Stagehand 更优 |
| **文档质量** | 一般              | 完善 (docs.stagehand.dev)   | ✅ Stagehand 更优 |
| **代码量**   | 需要手写任务描述  | 更简洁的 API                | ✅ Stagehand 更优 |

---

## 5. 集成架构建议

### 5.1 混合模式架构

```text
┌─────────────────────────────────────────────────────────────────────┐
│                     CreatorFlow 浏览器自动化层                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    策略选择器 (Router)                         │ │
│  │                                                               │ │
│  │  if 首次登录:                                                  │ │
│  │      use CDP + 真实浏览器 (最高反检测)                          │ │
│  │  elif 账号同步/信息获取:                                        │ │
│  │      use Stagehand extract() (AI 提取 + 自愈)                  │ │
│  │  elif 作品发布:                                                │ │
│  │      use Stagehand agent() (多步骤任务)                        │ │
│  │  else:                                                         │ │
│  │      fallback to Playwright + Stealth                          │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│         ┌────────────────────┼────────────────────┐                │
│         ▼                    ▼                    ▼                │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐        │
│  │   CDP Mode  │      │  Stagehand  │      │  Playwright │        │
│  │ (真实浏览器) │      │   (AI+自愈) │      │  + Stealth  │        │
│  └─────────────┘      └─────────────┘      └─────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 代码示例

```python
class HybridBrowserManager:
    """混合浏览器管理器 - 结合两种方案的优势"""

    async def login(self, platform: str, account_id: str):
        # 🔥 首次登录使用 CDP 真实浏览器 (最高反检测)
        return await self.cdp_manager.launch_and_connect(...)

    async def sync_profile(self, platform: str, account_id: str) -> UserProfile:
        # 🔥 账号同步使用 Stagehand (AI 提取 + 自愈)
        stagehand = Stagehand(StagehandConfig(env="LOCAL"))
        await stagehand.init()
        return await stagehand.page.extract(
            "提取用户名、头像、粉丝数",
            schema=UserProfile
        )

    async def publish(self, platform: str, content: dict):
        # 🔥 发布使用 Stagehand Agent (多步骤任务)
        await stagehand.agent.execute(
            f"在{platform}发布内容，标题: {content['title']}"
        )
```

---

## 6. 潜在风险

### 6.1 LLM Token 成本

> [!WARNING]
> 每次 `act()/extract()` 调用都会消耗 LLM token

**缓解措施**:

- 高频操作启用动作缓存
- 使用 Gemini Flash 等低成本模型
- 对可预测页面使用 Playwright 选择器

### 6.2 反检测能力

> [!CAUTION]
> Stagehand 本地模式使用 Playwright，反检测能力不如 CDP 真实浏览器

**缓解措施**:

- 首次登录/敏感操作使用 CDP 模式
- Stagehand 仅用于已登录后的操作
- 结合 playwright-stealth 增强反检测

---

## 7. 推荐场景

| 场景         | 推荐方案                | 原因                  |
| ------------ | ----------------------- | --------------------- |
| **首次登录** | CDP 真实浏览器          | 最高反检测能力        |
| **账号同步** | Stagehand `extract()`   | 结构化数据提取 + 自愈 |
| **作品发布** | Stagehand `agent()`     | 多步骤任务自动化      |
| **数据采集** | Stagehand `observe()`   | 智能元素发现          |
| **高频操作** | Playwright + 缓存选择器 | 避免 LLM 成本         |

---

## 8. 结论

### 8.1 是否推荐集成 Stagehand？

**✅ 推荐集成**，理由如下：

| 优势               | 说明                                       |
| ------------------ | ------------------------------------------ |
| **维护成本降低**   | 自愈能力减少了因平台 UI 变化导致的脚本维护 |
| **开发效率提升**   | 自然语言 API 比手写选择器快 5-10x          |
| **数据提取可靠**   | Pydantic Schema 确保结构化输出             |
| **与现有架构兼容** | 底层使用 Playwright，可与现有代码共存      |
| **本地运行**       | `env="LOCAL"` 无需付费云服务               |

### 8.2 最终推荐策略

**Stagehand + CDP 混合模式**:

1. **首次登录**: 使用 CDP 真实浏览器 (最高反检测)
2. **账号同步/数据提取**: 使用 Stagehand `extract()` (自愈 + 结构化)
3. **作品发布**: 使用 Stagehand `agent()` (多步骤任务)
4. **Fallback**: Playwright + Stealth (无 LLM 成本)

---

## 相关文档

- [浏览器自动化评估报告](file:///Users/mac/saas/ai-creator/docs/04-浏览器自动化评估报告.md)
- [Stagehand 官方文档](https://docs.stagehand.dev)
- [Stagehand Python SDK](https://github.com/browserbase/stagehand-python)
- [系统架构](file:///Users/mac/saas/ai-creator/docs/01-系统架构.md)
