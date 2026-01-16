use async_trait::async_trait;
use serde::Deserialize;
use crate::db::Repository;
use crate::sync::{ApiClient, providers::SyncProvider};

pub struct UserProvider;

#[derive(Deserialize)]
struct ApiUser {
    id: i64,
    username: String,
    nickname: String,
    email: Option<String>,
    avatar: Option<String>,
}

#[derive(Deserialize)]
struct ApiResponse {
    data: ApiUser,
}

#[async_trait]
impl SyncProvider for UserProvider {
    fn name(&self) -> &'static str {
        "User"
    }

    async fn pull(&self, client: &ApiClient, repo: &Repository, user_id: &str, token: &str) -> Result<(), String> {
        // 获取当前用户信息
        // API 返回结构: { code: 200, data: { ...user } }
        let resp: ApiResponse = client.get("/sys/users/me", Some(token)).await?;
        let user = resp.data;
        
        // 确保 ID 匹配 (虽然理论上 token 决定了 user，但作为校验)
        if user.id.to_string() != user_id {
            eprintln!("[UserProvider] Warning: API user ID {} does not match requested ID {}", user.id, user_id);
        }

        // 同步到本地数据库
        // 这将执行 UPSERT 操作，确保用户存在且信息最新
        repo.sync_user(
            &user.id.to_string(),
            user.email.as_deref(),
            Some(&user.username),
            Some(&user.nickname),
            user.avatar.as_deref()
        ).map_err(|e| e.to_string())?;
        
        Ok(())
    }

    async fn push(&self, _client: &ApiClient, _repo: &Repository, _user_id: &str, _token: &str) -> Result<(), String> {
        // 用户信息通常在设置页更新，这里暂不处理自动推送
        Ok(())
    }
}
