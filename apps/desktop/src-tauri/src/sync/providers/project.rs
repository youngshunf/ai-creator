//! 项目同步提供者

use async_trait::async_trait;
use serde::Deserialize;
use serde_json::Value;
use crate::db::Repository;
use crate::sync::{ApiClient, providers::SyncProvider};

pub struct ProjectProvider;

#[derive(Debug, Deserialize)]
struct ApiProject {
    id: String,
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
            repo.sync_project(
                &p.id,
                user_id,
                &p.name,
                p.description.as_deref(),
            ).map_err(|e| e.to_string())?;
        }

        Ok(())
    }

    async fn push(&self, client: &ApiClient, repo: &Repository, user_id: &str, token: &str) -> Result<(), String> {
        fn parse_list(value: &Option<String>) -> Vec<String> {
            value
                .as_ref()
                .and_then(|v| serde_json::from_str::<Vec<String>>(v).ok())
                .unwrap_or_default()
        }

        #[derive(Deserialize)]
        struct CreateResponse {
            data: ApiProject,
        }

        let projects = repo
            .list_pending_projects(user_id)
            .map_err(|e| e.to_string())?;

        for p in projects {
            let body = serde_json::json!({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "industry": p.industry,
                "sub_industries": parse_list(&p.sub_industries),
                "brand_name": p.brand_name,
                "brand_tone": p.brand_tone,
                "brand_keywords": parse_list(&p.brand_keywords),
                "topics": parse_list(&p.topics),
                "keywords": parse_list(&p.keywords),
                "account_tags": parse_list(&p.account_tags),
                "preferred_platforms": parse_list(&p.preferred_platforms),
                "content_style": p.content_style,
            });

            // 端云 ID 一致，先尝试 PUT 更新，如果不存在则 POST 创建
            let path = format!("/projects/{}", p.id);
            let result: Result<Value, String> = client.put(&path, &body, Some(token)).await;
            
            if result.is_err() {
                // 不存在，创建新项目
                let resp: CreateResponse = client.post("/projects", &body, Some(token)).await?;
                if resp.data.id != p.id {
                    return Err("Project sync failed: id mismatch".to_string());
                }
            }
            
            repo.mark_project_synced(&p.id).map_err(|e| e.to_string())?;
        }

        Ok(())
    }
}
