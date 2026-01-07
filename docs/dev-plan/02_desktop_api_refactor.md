# Desktop API Refactoring Plan

## Goal
Standardize API requests in the desktop application by encapsulating a unified interface request mechanism in TypeScript for UI-driven operations, while maintaining specific Tauri commands for agentic AI tasks. Ensure authentication state is synchronized between the Desktop UI and the Python Agent Sidecar.

## User Review Required
> [!IMPORTANT]
> **Hybrid Approach**:
> 1. **UI/CMS Operations**: Will use `axios` (TypeScript) directly connecting to Cloud Backend. This provides a better developer experience and consistency with the Web Frontend.
> 2. **AI Agent Operations**: Will continue using Tauri Commands (`invoke`) to communicate with the Python Sidecar.
> 3. **Token Synchronization**: The Desktop UI will be the "Source of Truth" for authentication. It will pass the valid `access_token` to the Sidecar when executing AI tasks, ensuring the Agent always has a fresh token.

## Proposed Changes

### Dependencies
- Install `axios` in `apps/desktop`.

### State Management
#### [MODIFY] `apps/desktop/src/stores/useAuthStore.ts`
- Enhance to handle full auth lifecycle (Login, Refresh, Logout).
- Persist `access_token`, `refresh_token`, and `user_info`.
- Add `getToken()` selector for easy access.

### API Layer (UI)
#### [NEW] `apps/desktop/src/api/request.ts`
- Create `axios` instance with interceptors:
    - **Request**: Inject `Authorization: Bearer <token>`.
    - **Response**: Handle 401. If unauthorized, attempt refresh. If refresh fails, logout and redirect. Global error toaster.

#### [NEW] `apps/desktop/src/api/`
- `auth.ts`: `login`, `logout`, `refreshToken`, `getUserInfo`.
- `project.ts`: Re-implement `getProjects`, `createProject`, `updateProject`, etc. using `axios`.
- `llm.ts`: `getModels` (can query backend directly), `getUsage`.

### operations (Agent)
#### [MODIFY] `apps/desktop/src-tauri/src/commands/mod.rs`
- Update `execute_ai_writing` (and `AIWritingRequest` struct) to accept `access_token`.
- Pass `access_token` to the Sidecar's `execute_graph` call.
- Remove `get_projects`, `create_project` etc. from Rust (once moved to TS).

### Sidecar/Agent Core
#### [MODIFY] `packages/agent-core/src/agent_core/llm/cloud_client.py`
- Ensure `CloudLLMClient` can accept an `access_token` dynamically per request or update its config in-memory, rather than solely relying on a static file load.

## Verification Plan
1.  **Login/Logout**: Verify flow using new Axios Auth API.
2.  **Project CRUD**: Verify Project management works via Axios.
3.  **Token Refresh**: Test auto-refresh by manipulating token expiry time.
4.  **AI Execution**:
    - Trigger "Start Writing".
    - Verify Frontend passes token to Tauri.
    - Verify Sidecar receives token and successfully calls Cloud LLM Gateway.
