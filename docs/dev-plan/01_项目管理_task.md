# 项目管理模块开发任务

## 一、云端 API 开发

### 1.1 数据模型 (Model)
- [x] 创建 `backend/app/project/` 模块目录
- [x] 创建 `model/project.py` - 项目数据模型 (基于 Base 类)

### 1.2 数据访问层 (CRUD)
- [x] 创建 `crud/crud_project.py` - 项目 CRUD 操作 (使用 CRUDPlus)

### 1.3 业务服务层 (Service)
- [x] 创建 `service/project_service.py` - 项目业务逻辑

### 1.4 Schema 定义
- [x] 创建 `schema/project.py` - 请求/响应模型定义

### 1.5 API 端点
- [x] 创建 `api/v1/project.py` - RESTful API 端点
- [x] 注册路由到主路由文件

### 1.6 单元测试
- [x] 创建 `tests/test_project.py` - API 测试用例

---

## 二、桌面端开发

### 2.1 状态管理
- [x] 创建 `stores/useProjectStore.ts` - 项目状态管理

### 2.2 UI 组件
- [x] 创建 `components/layout/ProjectSelector.tsx` - 项目选择器组件
- [x] 更新 `Header.tsx` - 集成项目选择器

### 2.3 项目设置页面
- [x] 创建 `routes/settings/project.tsx` - 项目设置页面

### 2.4 Tauri Commands
- [x] 添加项目相关命令到 `commands/mod.rs`
- [x] 注册命令到 `lib.rs`

---

## 三、验证

- [ ] 运行云端 API 测试
- [ ] 手动验证项目 CRUD 功能
- [ ] 验证项目切换功能
