//! 平台账号同步提供者

use async_trait::async_trait;
use serde::Deserialize;
use crate::db::Repository;
use crate::sync::{ApiClient, providers::SyncProvider};

pub struct AccountProvider;

#[derive(Debug, Deserialize)]
struct ApiAccount {
    // id: i64, // 数据库自增ID，通常不需要同步到本地，除非作为关联键
    // uuid: String, // 如果有 UUID
    project_id: i64, // 这里可能是 int ID，需要映射到本地 UUID
    project_uuid: Option<String>, // 假设 API 返回了 project_uuid
    platform: String,
    account_id: String,
    account_name: Option<String>,
    avatar: Option<String>,
    followers_count: Option<i64>,
    following_count: Option<i64>,
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
        struct AccountData {
            items: Vec<ApiAccount>,
        }

        #[derive(Deserialize)]
        struct ApiResponse {
            data: AccountData,
        }

        // 假设有一个获取所有账号的端点，或者按项目获取
        // 这里简化为获取所有账号
        // 注意：实际 API 可能需要分页或按项目过滤
        let resp: ApiResponse = client.get("/platform-accounts", Some(token)).await.or_else(|e| {
             // 如果没有全局接口，暂时返回空列表，避免阻塞其他同步
             eprintln!("[AccountProvider] Error fetching accounts: {}", e);
             Ok::<ApiResponse, String>(ApiResponse { 
                 data: AccountData { items: vec![] } 
             })
        })?;
        
        eprintln!("[AccountProvider] Received {} accounts from cloud", resp.data.items.len());
        
        // 修正：遍历 resp.data.items
        for acc in resp.data.items {
            eprintln!("[AccountProvider] Processing account: {} ({}) for project_id: {}", acc.account_id, acc.platform, acc.project_id);

            // 需要 Project UUID
            // 尝试从 project_uuid 获取，如果为空，则尝试通过 project_id (int) 查找本地映射
            let project_id = if let Some(uuid) = acc.project_uuid {
                uuid
            } else {
                // 尝试通过 cloud_id 查找
                if let Ok(Some(uuid)) = repo.get_project_uuid_by_cloud_id(acc.project_id) {
                    uuid
                } else {
                    // 无法关联到项目，跳过
                    eprintln!("[AccountProvider] Warning: Skipping account {} because project_id {}/uuid {:?} not found locally", 
                        acc.account_id, acc.project_id, acc.project_uuid);
                    continue;
                }
            };

            // 确保项目存在
            repo.ensure_project_exists(&project_id, user_id).map_err(|e| e.to_string())?;

            // 创建或更新账号
            let _ = repo.create_platform_account(
                user_id,
                &project_id,
                &acc.platform,
                &acc.account_id,
                acc.account_name.as_deref()
            ).map_err(|e| e.to_string())?;
            
            eprintln!("[AccountProvider] Successfully synced account: {}", acc.account_id);

            // 更新资料
            // ...
        }

        Ok(())
    }

    async fn push(&self, _client: &ApiClient, _repo: &Repository, _user_id: &str, _token: &str) -> Result<(), String> {
        // 账号通常不在本地创建，而是在 Sidecar 登录后同步
        // 但如果有资料更新（如备注名），可以 Push
        Ok(())
    }
}
