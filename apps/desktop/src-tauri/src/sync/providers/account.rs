//! 平台账号同步提供者

use async_trait::async_trait;
use serde::Deserialize;
use serde_json;
use crate::db::Repository;
use crate::sync::{ApiClient, providers::SyncProvider};

pub struct AccountProvider;

/// 云端返回的平台账号信息
#[derive(Debug, Deserialize)]
struct ApiAccount {
    // id: i64, // 数据库自增ID
    // uuid: String, // 账号 UUID
    project_id: i64, // 云端项目 ID (int)
    project_uuid: String, // 项目 UUID
    platform: String,
    account_id: String,
    account_name: Option<String>,
    avatar_url: Option<String>,
    followers_count: Option<i64>,
    following_count: Option<i64>,
    posts_count: Option<i64>,
    is_active: Option<bool>,
    session_valid: Option<bool>,
    metadata_info: Option<serde_json::Value>,
}

#[async_trait]
impl SyncProvider for AccountProvider {
    fn name(&self) -> &'static str {
        "PlatformAccount"
    }

    async fn pull(&self, client: &ApiClient, repo: &Repository, user_id: &str, token: &str) -> Result<(), String> {
        // 0. 确保用户存在
        repo.ensure_user_exists(user_id).map_err(|e| e.to_string())?;

        // 1. 获取账号列表
        #[derive(Deserialize)]
        struct ApiResponse {
            data: Vec<ApiAccount>,
        }

        // 调用 /api/v1/platform-accounts 获取当前用户的所有平台账号
        let resp: ApiResponse = client.get("/platform-accounts", Some(token)).await.or_else(|e| {
            eprintln!("[AccountProvider] Error fetching accounts: {}", e);
            Ok::<ApiResponse, String>(ApiResponse { data: vec![] })
        })?;
        
        eprintln!("[AccountProvider] Received {} accounts from cloud", resp.data.len());
        
        for acc in resp.data {
            eprintln!("[AccountProvider] Processing account: {} ({}) for project_uuid: {}", 
                acc.account_id, acc.platform, acc.project_uuid);

            // 确保项目存在
            repo.ensure_project_exists(&acc.project_uuid, user_id).map_err(|e| e.to_string())?;

            // 创建或更新账号
            let local_account = repo.create_platform_account(
                user_id,
                &acc.project_uuid,
                &acc.platform,
                &acc.account_id,
                acc.account_name.as_deref()
            ).map_err(|e| e.to_string())?;
            
            // 更新账号资料（包括扩展字段）
            let metadata_str = acc.metadata_info.map(|v| v.to_string());
            let _ = repo.update_platform_account_profile(
                &local_account.id,
                acc.account_name.as_deref(),
                acc.avatar_url.as_deref(),
                acc.followers_count.unwrap_or(0),
                acc.following_count.unwrap_or(0),
                acc.posts_count.unwrap_or(0),
                metadata_str.as_deref(),
            ).map_err(|e| e.to_string())?;
            
            eprintln!("[AccountProvider] Successfully synced account: {} with profile", acc.account_id);
        }

        Ok(())
    }

    async fn push(&self, _client: &ApiClient, _repo: &Repository, _user_id: &str, _token: &str) -> Result<(), String> {
        // 账号通常不在本地创建，而是在 Sidecar 登录后同步
        // 但如果有资料更新（如备注名），可以 Push
        Ok(())
    }
}
