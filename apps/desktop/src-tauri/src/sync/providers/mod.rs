//! 同步提供者 Trait 定义

pub mod account;
pub mod project;
pub mod user;

pub use account::AccountProvider;
pub use project::ProjectProvider;
pub use user::UserProvider;

use async_trait::async_trait;
use crate::db::Repository;
use crate::sync::ApiClient;

/// 同步提供者 Trait
/// 任何需要同步的数据类型都必须实现此 Trait
#[async_trait]
pub trait SyncProvider: Send + Sync {
    /// 数据类型名称 (用于日志)
    fn name(&self) -> &'static str;

    /// 执行拉取操作 (云端 -> 本地)
    async fn pull(&self, client: &ApiClient, repo: &Repository, user_id: &str, token: &str) -> Result<(), String>;

    /// 执行推送操作 (本地 -> 云端)
    async fn push(&self, client: &ApiClient, repo: &Repository, user_id: &str, token: &str) -> Result<(), String>;
}
