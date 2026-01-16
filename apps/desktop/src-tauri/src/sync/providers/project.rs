//! 项目同步提供者

use async_trait::async_trait;
use serde::Deserialize;
use crate::db::Repository;
use crate::sync::{ApiClient, providers::SyncProvider};

pub struct ProjectProvider;

#[derive(Debug, Deserialize)]
struct ApiProject {
    id: i64,
    uuid: String,
    name: String,
    description: Option<String>,
    // TODO: 添加更多字段
}

#[async_trait]
impl SyncProvider for ProjectProvider {
    fn name(&self) -> &'static str {
        "Project"
    }

    async fn pull(&self, client: &ApiClient, repo: &Repository, user_id: &str, token: &str) -> Result<(), String> {
        // 0. 确保用户存在 (避免外键错误)
        repo.ensure_user_exists(user_id).map_err(|e| e.to_string())?;

        // 1. 从 API 获取项目列表
        // 假设 API 返回标准响应结构 { code: 200, data: { items: [...], total: ... } }
        #[derive(Deserialize)]
        struct ProjectData {
            items: Vec<ApiProject>,
        }

        #[derive(Deserialize)]
        struct ApiResponse {
            data: ProjectData,
        }

        let resp: ApiResponse = client.get("/projects", Some(token)).await?;
        
        // 2. 更新本地数据库
        for p in resp.data.items {
            // 注意：这里使用 uuid 作为本地 id (string)，因为本地使用 uuid 字符串作为主键
            // 同时保存 p.id 到 cloud_id，以便 AccountProvider 关联
            repo.sync_project(
                &p.uuid,
                user_id,
                &p.name,
                p.description.as_deref(),
                Some(p.id)
            ).map_err(|e| e.to_string())?;
        }

        Ok(())
    }

    async fn push(&self, _client: &ApiClient, _repo: &Repository, _user_id: &str, _token: &str) -> Result<(), String> {
        // TODO: 实现推送逻辑
        // 1. 查询 sync_status = 'pending' 的项目
        // 2. 逐个上传
        // 3. 更新 sync_status = 'synced'
        Ok(())
    }
}
