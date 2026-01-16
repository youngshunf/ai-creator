# 实施计划：云端账号信息同步功能

我将实现云端账号信息同步功能，重点是**完整实现桌面端 `apps/desktop/src/api/account.ts` 中定义的所有 5 个接口**，以及相应的云端管理页面。

## 1. 云端后端开发 (`services/cloud-backend`)

我将在 `app/project` 模块下实现以下 API，确保与桌面端接口定义完全匹配：

- **URL 路径前缀**: `/api/v1/projects/{project_id}/accounts`
- **待实现接口**:
  1.  **获取列表 (`GET /`)**: 对应 `getAccountsApi`。
  2.  **创建账号 (`POST /`)**: 对应 `createAccountApi`。接收平台、账号ID、名称等信息。
  3.  **更新账号 (`PUT /{account_id}`)**: 对应 `updateAccountApi`。更新粉丝数、头像等。
  4.  **删除账号 (`DELETE /{account_id}`)**: 对应 `deleteAccountApi`。
  5.  **同步账号 (`POST /sync`)**: 对应 `syncAccountToCloudApi`。这是一个 Upsert 操作，如果账号存在则更新，不存在则创建，并更新同步时间。

- **开发步骤**:
  1.  **Model**: 创建 `app/project/model/platform_account.py`。
  2.  **Schema**: 创建 `app/project/schema/platform_account.py` (包含 Create, Update, Sync schema)。
  3.  **CRUD**: 创建 `app/project/crud/crud_platform_account.py`。
  4.  **Service**: 创建 `app/project/service/platform_account_service.py`。
  5.  **API**: 创建 `app/project/api/v1/platform_account.py` 并注册路由。

## 2. 云端前端开发 (`services/cloud-frontend`)

我将在管理后台添加页面，用于查看通过上述接口同步上来的数据。

- **API 定义**:
  - 在 `apps/web-antd/src/api/project` 下创建 `account.ts`，复用后端的 CRUD 接口。
- **页面视图**:
  - 新建 `apps/web-antd/src/views/project/account/index.vue`。
  - 实现一个表格，展示：所属项目、平台、账号名称、粉丝数、最近同步时间。
- **路由**:
  - 配置菜单路由，使其在“项目管理”下可见。

## 3. 验证计划

- **接口测试**: 使用 `curl` 或 Postman 模拟桌面端发出的请求，验证 5 个接口是否正常工作。
- **页面验证**: 在云端管理后台查看是否能正确显示模拟插入的数据。

该计划将确保桌面端的同步逻辑（如 `useAccountStore.ts` 中的调用）能够成功与云端交互。
