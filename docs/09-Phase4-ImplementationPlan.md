# Phase 4: A2UI 富交互 UI 集成 实施计划

## 目标
实现 Agent 与用户之间的**富交互 UI**：Agent 可以通过发送 JSON 描述来生成可交互的 UI 组件（如表单、按钮、卡片），用户提交后数据回传给 Agent，形成闭环。

## 用户审阅事项
> [!IMPORTANT]
> Phase 4 涉及 **前端 (React/TypeScript)** 和 **后端 (Python)** 的协同修改。

---

## 提议的修改

### 1. 后端 (agent-core): 定义 UI 协议

#### [NEW] `packages/agent-core/src/agent_core/ui/protocol.py`
定义 `UIComponent` 和 `UIMessage` 数据结构 (Pydantic 模型):
```python
class UIComponent:
    type: str  # 'card', 'text', 'button', 'input', 'form', 'table', 'markdown'
    props: dict  # 组件属性
    children: list[UIComponent] | None
    events: dict | None  # {'onClick': 'action_id'}

class UIMessage:
    ui: UIComponent
    expects_response: bool  # 是否等待用户交互
```

#### [NEW] `packages/agent-core/src/agent_core/runtime/events.py` 增强
新增 `EventType.UI_RENDER` 事件类型。

#### [NEW] `agent-definitions/skills/ui-generator.md`
创建 `ui-generator` Skill，包含生成 UI JSON 的指令和示例。

---

### 2. 前端 (apps/desktop): 实现 UI 渲染器

#### [NEW] `apps/desktop/src/components/a2ui/NativeUIRenderer.tsx`
核心渲染组件，接收 `UIComponent` JSON 并递归渲染为 React 组件。

#### [NEW] `apps/desktop/src/components/a2ui/componentMap.ts`
组件映射表，将 `type` 字符串映射到具体的 React 组件。

#### [MODIFY] `apps/desktop/src/components/chat/ChatMessage.tsx` (或类似组件)
当消息类型为 `UI_RENDER` 时，调用 `NativeUIRenderer` 进行渲染。

---

### 3. 通讯闭环 (交互回传)

#### [MODIFY] `apps/desktop/src/hooks/useAgentChat.ts` (或类似 Hook)
当用户在 UI 组件上触发事件（如表单提交），将事件数据发送回 Sidecar。

#### [NEW/MODIFY] `apps/sidecar/src/sidecar/executor.py`
处理来自前端的用户交互事件，恢复暂停的 Agent 执行流程。

---

## 验证计划

### 手动验证 (推荐)
1.  启动 Sidecar: `uv run python -m sidecar.main` (或项目特定启动方式)。
2.  启动桌面端: `pnpm --filter desktop dev`。
3.  在聊天界面输入: "帮我生成一个简单的用户调查表单"。
4.  **预期**: 聊天界面中出现一个可交互的表单（输入框 + 提交按钮）。
5.  填写表单并提交。
6.  **预期**: Agent 收到表单数据并做出响应。

### 单元测试 (可选)
- `packages/agent-core/tests/test_ui_protocol.py`: 验证 `UIComponent` 序列化/反序列化。
- 前端测试 (如 Vitest/Jest): 验证 `NativeUIRenderer` 渲染不同 `type` 的组件。

---

## 实现顺序
1.  **后端**: 定义 `ui/protocol.py` 和 `EventType.UI_RENDER`。
2.  **前端**: 实现 `NativeUIRenderer` 和 `componentMap`。
3.  **Skill**: 创建 `ui-generator.md`。
4.  **集成测试**: 手动在桌面端测试 Agent 生成 UI 的能力。
