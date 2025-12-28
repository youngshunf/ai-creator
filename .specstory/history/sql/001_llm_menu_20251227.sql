-- =====================================================
-- LLM 管理模块菜单初始化 SQL
-- @author Ysf
-- @date 2025-12-27
-- =====================================================

-- 删除已存在的 LLM 菜单（如需重新初始化）
-- DELETE FROM sys_menu WHERE name LIKE 'Llm%';

-- LLM 管理一级菜单
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
VALUES
(100, 'LLM 管理', 'Llm', '/llm', 5, 'carbon:machine-learning-model', 0, NULL, NULL, 1, 1, 1, '', 'LLM 大语言模型管理模块', NULL, NOW(), NULL);

-- LLM 供应商管理
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
VALUES
(101, '供应商管理', 'LlmProvider', '/llm/provider', 1, 'carbon:cloud-service-management', 1, '/llm/provider/index', NULL, 1, 1, 1, '', 'LLM 供应商管理', 100, NOW(), NULL),
(102, '新增', 'AddLlmProvider', NULL, 0, NULL, 2, NULL, 'llm:provider:add', 1, 0, 1, '', NULL, 101, NOW(), NULL),
(103, '修改', 'EditLlmProvider', NULL, 0, NULL, 2, NULL, 'llm:provider:edit', 1, 0, 1, '', NULL, 101, NOW(), NULL),
(104, '删除', 'DeleteLlmProvider', NULL, 0, NULL, 2, NULL, 'llm:provider:del', 1, 0, 1, '', NULL, 101, NOW(), NULL);

-- LLM 模型配置
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
VALUES
(105, '模型配置', 'LlmModel', '/llm/model', 2, 'carbon:model-alt', 1, '/llm/model/index', NULL, 1, 1, 1, '', 'LLM 模型配置管理', 100, NOW(), NULL),
(106, '新增', 'AddLlmModel', NULL, 0, NULL, 2, NULL, 'llm:model:add', 1, 0, 1, '', NULL, 105, NOW(), NULL),
(107, '修改', 'EditLlmModel', NULL, 0, NULL, 2, NULL, 'llm:model:edit', 1, 0, 1, '', NULL, 105, NOW(), NULL),
(108, '删除', 'DeleteLlmModel', NULL, 0, NULL, 2, NULL, 'llm:model:del', 1, 0, 1, '', NULL, 105, NOW(), NULL);

-- LLM 模型组
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
VALUES
(109, '模型组', 'LlmModelGroup', '/llm/model-group', 3, 'carbon:group-objects', 1, '/llm/model-group/index', NULL, 1, 1, 1, '', 'LLM 模型组管理', 100, NOW(), NULL),
(110, '新增', 'AddLlmModelGroup', NULL, 0, NULL, 2, NULL, 'llm:model-group:add', 1, 0, 1, '', NULL, 109, NOW(), NULL),
(111, '修改', 'EditLlmModelGroup', NULL, 0, NULL, 2, NULL, 'llm:model-group:edit', 1, 0, 1, '', NULL, 109, NOW(), NULL),
(112, '删除', 'DeleteLlmModelGroup', NULL, 0, NULL, 2, NULL, 'llm:model-group:del', 1, 0, 1, '', NULL, 109, NOW(), NULL);

-- LLM 速率限制配置
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
VALUES
(113, '速率限制', 'LlmRateLimit', '/llm/rate-limit', 4, 'carbon:meter', 1, '/llm/rate-limit/index', NULL, 1, 1, 1, '', 'LLM 速率限制配置', 100, NOW(), NULL),
(114, '新增', 'AddLlmRateLimit', NULL, 0, NULL, 2, NULL, 'llm:rate-limit:add', 1, 0, 1, '', NULL, 113, NOW(), NULL),
(115, '修改', 'EditLlmRateLimit', NULL, 0, NULL, 2, NULL, 'llm:rate-limit:edit', 1, 0, 1, '', NULL, 113, NOW(), NULL),
(116, '删除', 'DeleteLlmRateLimit', NULL, 0, NULL, 2, NULL, 'llm:rate-limit:del', 1, 0, 1, '', NULL, 113, NOW(), NULL);

-- LLM API Key 管理
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
VALUES
(117, 'API Key 管理', 'LlmApiKey', '/llm/api-key', 5, 'carbon:password', 1, '/llm/api-key/index', NULL, 1, 1, 1, '', 'LLM API Key 管理', 100, NOW(), NULL),
(118, '新增', 'AddLlmApiKey', NULL, 0, NULL, 2, NULL, 'llm:api-key:add', 1, 0, 1, '', NULL, 117, NOW(), NULL),
(119, '修改', 'EditLlmApiKey', NULL, 0, NULL, 2, NULL, 'llm:api-key:edit', 1, 0, 1, '', NULL, 117, NOW(), NULL),
(120, '删除', 'DeleteLlmApiKey', NULL, 0, NULL, 2, NULL, 'llm:api-key:del', 1, 0, 1, '', NULL, 117, NOW(), NULL);

-- LLM 用量统计
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time)
VALUES
(121, '用量统计', 'LlmUsage', '/llm/usage', 6, 'carbon:analytics', 1, '/llm/usage/index', NULL, 1, 1, 1, '', 'LLM 用量统计', 100, NOW(), NULL),
(122, '查看', 'ViewLlmUsage', NULL, 0, NULL, 2, NULL, 'llm:usage:view', 1, 0, 1, '', NULL, 121, NOW(), NULL);

-- =====================================================
-- 为管理员角色分配 LLM 菜单权限（可选）
-- 假设管理员角色 ID 为 1
-- =====================================================
-- INSERT INTO sys_role_menu (role_id, menu_id)
-- SELECT 1, id FROM sys_menu WHERE id BETWEEN 100 AND 122;
