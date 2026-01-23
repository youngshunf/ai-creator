//! 项目私有选题同步提供者

use async_trait::async_trait;
use serde::Deserialize;
use serde_json::Value;

use crate::db::Repository;
use crate::sync::{ApiClient, providers::SyncProvider};


pub struct ProjectTopicProvider;


#[async_trait]
impl SyncProvider for ProjectTopicProvider {
    fn name(&self) -> &'static str {
        "ProjectTopic"
    }

    async fn pull(&self, client: &ApiClient, repo: &Repository, user_id: &str, token: &str) -> Result<(), String> {
        #[derive(Deserialize)]
        struct ApiResponse {
            data: Vec<Value>,
        }

        let projects = repo.list_projects(user_id).map_err(|e| e.to_string())?;
        for p in projects {
            // 使用项目 ID (UUID 字符串) 作为路径参数
            let path = format!("/projects/{}/topics", p.id);
            let resp: ApiResponse = client.get(&path, Some(token)).await?;

            for item in resp.data {
                // 云端现在也用 id 作为主键
                let topic_id = item.get("id").and_then(|v| v.as_str()).unwrap_or("").to_string();
                if topic_id.trim().is_empty() {
                    continue;
                }
                let title = item.get("title").and_then(|v| v.as_str()).unwrap_or("").to_string();
                let batch_date = item.get("batch_date").and_then(|v| v.as_str()).map(|s| s.to_string());
                let source_uid = item.get("source_uid").and_then(|v| v.as_str()).map(|s| s.to_string());
                let status = item.get("status").and_then(|v| v.as_i64()).unwrap_or(0);
                let server_version = item.get("server_version").and_then(|v| v.as_i64()).unwrap_or(0);
                let is_deleted = item.get("is_deleted").and_then(|v| v.as_bool()).unwrap_or(false);

                let payload = item.to_string();
                repo.sync_project_topic(
                    &topic_id,
                    user_id,
                    &p.id,
                    &title,
                    &payload,
                    batch_date.as_deref(),
                    source_uid.as_deref(),
                    status,
                    server_version,
                    is_deleted,
                    None,
                )
                .map_err(|e| e.to_string())?;
            }
        }

        Ok(())
    }

    async fn push(&self, client: &ApiClient, repo: &Repository, user_id: &str, token: &str) -> Result<(), String> {
        #[derive(Deserialize)]
        struct ApiResponse {
            data: Vec<Value>,
        }

        let projects = repo.list_projects(user_id).map_err(|e| e.to_string())?;
        for p in projects {
            let pending = repo
                .list_pending_project_topics(&p.id)
                .map_err(|e| e.to_string())?;
            if pending.is_empty() {
                continue;
            }

            let mut topics: Vec<Value> = Vec::new();
            for t in pending.iter() {
                let mut item: Value = serde_json::from_str(&t.payload).unwrap_or_else(|_| serde_json::json!({}));
                if !item.is_object() {
                    item = serde_json::json!({});
                }

                let obj = item.as_object_mut().unwrap();
                // 端云 ID 统一，使用 id 作为主键
                obj.insert("id".to_string(), Value::String(t.id.clone()));
                if let Some(batch_date) = &t.batch_date {
                    obj.insert("batch_date".to_string(), Value::String(batch_date.clone()));
                } else {
                    obj.insert("batch_date".to_string(), Value::Null);
                }
                if let Some(source_uid) = &t.source_uid {
                    obj.insert("source_uid".to_string(), Value::String(source_uid.clone()));
                } else {
                    obj.insert("source_uid".to_string(), Value::Null);
                }
                obj.insert("status".to_string(), serde_json::json!(t.status));
                obj.insert("is_deleted".to_string(), Value::Bool(t.is_deleted));
                obj.insert("deleted_at".to_string(), Value::Null);

                for key in [
                    "keywords",
                    "heat_sources",
                    "industry_tags",
                    "creative_angles",
                    "format_suggestions",
                    "risk_notes",
                ] {
                    if !obj.contains_key(key) {
                        obj.insert(key.to_string(), serde_json::json!([]));
                    }
                }
                for key in ["platform_heat", "trend", "source_info"] {
                    if !obj.contains_key(key) {
                        obj.insert(key.to_string(), serde_json::json!({}));
                    }
                }
                for key in ["target_audience", "content_outline", "material_clues"] {
                    if !obj.contains_key(key) {
                        obj.insert(key.to_string(), serde_json::json!([]));
                    }
                }

                if !obj.contains_key("title") {
                    obj.insert("title".to_string(), Value::String(t.title.clone()));
                }
                if !obj.contains_key("potential_score") {
                    obj.insert("potential_score".to_string(), serde_json::json!(0.0));
                }
                if !obj.contains_key("heat_index") {
                    obj.insert("heat_index".to_string(), serde_json::json!(0.0));
                }
                if !obj.contains_key("reason") {
                    obj.insert("reason".to_string(), Value::String(String::new()));
                }

                topics.push(Value::Object(obj.clone()));
            }

            // 使用项目 ID (UUID 字符串) 作为路径参数
            let path = format!("/projects/{}/topics/sync", p.id);
            let body = serde_json::json!({ "topics": topics });
            let resp: ApiResponse = client
                .post(&path, &body, Some(token))
                .await?;

            for item in resp.data {
                let topic_id = item.get("id").and_then(|v| v.as_str()).unwrap_or("");
                if topic_id.trim().is_empty() {
                    continue;
                }
                let server_version = item.get("server_version").and_then(|v| v.as_i64()).unwrap_or(0);
                repo.mark_project_topic_synced(topic_id, server_version)
                    .map_err(|e| e.to_string())?;
            }
        }

        Ok(())
    }
}
