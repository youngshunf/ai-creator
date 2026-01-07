# 项目管理模块实现计划

> 需求来源: `docs/dev-plan/01_项目管理.md`
> 版本: v1.0 | 日期: 2026-01-05

## 目标描述

实现项目管理模块的完整功能，包括：
- 云端 API：项目 CRUD 接口
- 桌面端 UI：项目选择器、项目设置页面
- 状态管理：Zustand store 管理项目状态

---

## Proposed Changes

### Cloud Backend (FastAPI)

新建 `project` 模块，遵循现有架构模式：Model → CRUD → Service → API

---

#### [NEW] [\_\_init\_\_.py](file:///Users/mac/saas/ai-creator/services/cloud-backend/backend/app/project/__init__.py)
模块入口文件

#### [NEW] [project.py](file:///Users/mac/saas/ai-creator/services/cloud-backend/backend/app/project/model/project.py)
项目数据模型，基于 `Base` 类，包含字段：
- `id`, `user_id`, `name`, `description`
- 行业领域：`industry`, `sub_industries`
- 品牌信息：`brand_name`, `brand_tone`, `brand_keywords`
- 内容定位：`topics`, `keywords`, `account_tags`
- 偏好设置：`preferred_platforms`, `content_style`, `settings`
- 同步字段：`server_version`, `is_default`, `is_deleted`

#### [NEW] [crud_project.py](file:///Users/mac/saas/ai-creator/services/cloud-backend/backend/app/project/crud/crud_project.py)
使用 `CRUDPlus` 实现项目 CRUD 操作

#### [NEW] [project_service.py](file:///Users/mac/saas/ai-creator/services/cloud-backend/backend/app/project/service/project_service.py)
业务逻辑封装，包含项目创建、更新、删除、设为默认等操作

#### [NEW] [project.py](file:///Users/mac/saas/ai-creator/services/cloud-backend/backend/app/project/schema/project.py)
Pydantic 模型定义：`ProjectCreate`, `ProjectUpdate`, `ProjectResponse`

#### [NEW] [project.py](file:///Users/mac/saas/ai-creator/services/cloud-backend/backend/app/project/api/v1/project.py)
RESTful API 端点：
| Method | Path | 描述 |
|--------|------|------|
| POST | `/api/v1/projects` | 创建项目 |
| GET | `/api/v1/projects` | 获取项目列表 |
| GET | `/api/v1/projects/{id}` | 获取项目详情 |
| PUT | `/api/v1/projects/{id}` | 更新项目 |
| DELETE | `/api/v1/projects/{id}` | 删除项目 |
| POST | `/api/v1/projects/{id}/set-default` | 设为默认项目 |

#### [MODIFY] [router.py](file:///Users/mac/saas/ai-creator/services/cloud-backend/backend/app/router.py)
注册 project 路由

---

### Desktop Frontend (React + Tauri)

---

#### [NEW] [useProjectStore.ts](file:///Users/mac/saas/ai-creator/apps/desktop/src/stores/useProjectStore.ts)
Zustand store，管理项目列表和当前项目状态

#### [NEW] [ProjectSelector.tsx](file:///Users/mac/saas/ai-creator/apps/desktop/src/components/layout/ProjectSelector.tsx)
项目选择器下拉组件，替换 Header 中的硬编码项目选择器

#### [MODIFY] [Header.tsx](file:///Users/mac/saas/ai-creator/apps/desktop/src/components/layout/Header.tsx)
集成 ProjectSelector 组件

#### [NEW] [project.tsx](file:///Users/mac/saas/ai-creator/apps/desktop/src/routes/settings/project.tsx)
项目设置页面，编辑项目信息

---

### Tauri Commands (Rust)

---

#### [MODIFY] [mod.rs](file:///Users/mac/saas/ai-creator/apps/desktop/src-tauri/src/commands/mod.rs)
添加项目相关命令：
- `get_projects` - 获取项目列表
- `create_project` - 创建项目
- `update_project` - 更新项目
- `delete_project` - 删除项目
- `set_current_project` - 设置当前项目

#### [MODIFY] [lib.rs](file:///Users/mac/saas/ai-creator/apps/desktop/src-tauri/src/lib.rs)
注册新命令到 invoke_handler

---

## Verification Plan

### Automated Tests

**云端 API 测试**:
```bash
cd services/cloud-backend
pytest backend/app/project/tests/test_project.py -v
```

测试用例包括：
1. 创建项目 - 验证返回正确的项目数据
2. 获取项目列表 - 验证分页和过滤
3. 更新项目 - 验证字段更新成功
4. 删除项目 - 验证软删除
5. 设为默认项目 - 验证只有一个默认项目

### Manual Verification

1. **创建项目**:
   - 启动桌面端应用
   - 点击 Header 中的项目选择器
   - 点击"创建新项目"
   - 填写项目名称、行业、品牌信息
   - 保存后验证项目出现在列表中

2. **切换项目**:
   - 点击项目选择器
   - 选择另一个项目
   - 验证当前项目显示已切换
   - 验证工作区上下文已更新

3. **项目隔离**:
   - 在项目 A 状态下创建内容
   - 切换到项目 B
   - 验证看不到项目 A 的内容

---

## Dependencies

- 云端 API 需要先开发完成，桌面端才能调用
- 需要确保 PostgreSQL 数据库已有 `projects` 表（或通过 Alembic 迁移创建）
