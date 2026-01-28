//! 平台账号同步提供者

use async_trait::async_trait;
use serde::Deserialize;
use serde_json;

use crate::db::Repository;
use crate::sync::{providers::SyncProvider, ApiClient};

pub struct AccountProvider;

    /// 云端返回的平台账号信息（PlatformAccountInfo）
    #[derive(Debug, Deserialize)]
    struct ApiAccount {
        /// 平台账号 UID（platform_accounts.uid）
        id: String,
        /// 账户所属用户 UID（sys_user.uuid）
        user_id: String,
        /// 关联项目 UID（projects.uid）
        project_id: String,
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
    is_deleted: bool,
    server_version: i64,
}

#[async_trait]
impl SyncProvider for AccountProvider {
    fn name(&self) -> &'static str {
        "PlatformAccount"
    }

    async fn pull(&self, client: &ApiClient, repo: &Repository, user_id: &str, token: &str) -> Result<(), String> {
        // 0. 确保用户存在
        repo.ensure_user_exists(user_id)
            .map_err(|e| e.to_string())?;

        // 1. 获取账号列表
        #[derive(Deserialize)]
        struct ApiResponse {
            data: Vec<ApiAccount>,
        }

        // 调用 /platform-accounts 获取当前用户的所有平台账号
        let resp: ApiResponse = client.get("/platform-accounts", Some(token)).await?;

        eprintln!(
            "[AccountProvider] Received {} accounts from cloud",
            resp.data.len()
        );

        for acc in resp.data {
            eprintln!(
                "[AccountProvider] Processing account: {} ({}) for project_id: {}",
                acc.account_id, acc.platform, acc.project_id
            );

            // 确保项目存在（按项目 UID 同一 ID）
            repo.ensure_project_exists(&acc.project_id, user_id)
                .map_err(|e| e.to_string())?;

            let metadata_str = acc.metadata_info.map(|v| v.to_string());

            // 云端/本地 ID 统一: 使用 id 作为主键
            repo.sync_platform_account(
                &acc.id,
                user_id,
                &acc.project_id,
                &acc.platform,
                &acc.account_id,
                acc.account_name.as_deref(),
                acc.avatar_url.as_deref(),
                acc.followers_count.unwrap_or(0),
                acc.following_count.unwrap_or(0),
                acc.posts_count.unwrap_or(0),
                acc.is_active.unwrap_or(true),
                acc.session_valid.unwrap_or(false),
                metadata_str.as_deref(),
                acc.is_deleted,
                acc.server_version,
            )
            .map_err(|e| e.to_string())?;

            eprintln!(
                "[AccountProvider] Successfully synced account: {} with profile",
                acc.account_id
            );
        }

        Ok(())
    }

    async fn push(&self, client: &ApiClient, repo: &Repository, user_id: &str, token: &str) -> Result<(), String> {
        #[derive(Debug, Deserialize)]
        struct ApiAccountResponse {
            id: String,
            project_id: String,
                        server_version: i64,
        }

        #[derive(Debug, Deserialize)]
        struct ApiResponse {
            data: ApiAccountResponse,
        }

        let accounts = repo
            .list_pending_platform_accounts(user_id)
            .map_err(|e| e.to_string())?;

        for acc in accounts {
            let path = format!("/projects/{}/accounts/sync", acc.project_id);
            let metadata = acc
                .metadata
                .as_ref()
                .and_then(|v| serde_json::from_str::<serde_json::Value>(v).ok())
                .unwrap_or_else(|| serde_json::json!({}));

            let body = serde_json::json!({
                "id": acc.id,
                "project_id": acc.project_id,
                "platform": acc.platform,
                "account_id": acc.account_id,
                "account_name": acc.account_name,
                "avatar_url": acc.avatar_url,
                "followers_count": acc.followers_count,
                "following_count": acc.following_count,
                "posts_count": acc.posts_count,
                "is_active": acc.is_active,
                "session_valid": acc.session_valid,
                "metadata_info": metadata,
                "is_deleted": acc.is_deleted,
            });

            let resp: ApiResponse = client.post(&path, &body, Some(token)).await?;

            if resp.data.id != acc.id {
                return Err("Platform account sync failed: id mismatch".to_string());
            }
            if resp.data.project_id != acc.project_id {
                return Err("Platform account sync failed: project_id mismatch".to_string());
            }

            repo
                .mark_platform_account_synced(&acc.id, resp.data.server_version)
                .map_err(|e| e.to_string())?;
        }

        Ok(())
    }
}
