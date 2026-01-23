//! 数据库模型定义
//! @author Ysf

use serde::{Deserialize, Serialize};

/// 同步状态
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub enum SyncStatus {
    #[default]
    Synced,
    Pending,
    Conflict,
}

impl From<&str> for SyncStatus {
    fn from(s: &str) -> Self {
        match s {
            "pending" => SyncStatus::Pending,
            "conflict" => SyncStatus::Conflict,
            _ => SyncStatus::Synced,
        }
    }
}

impl ToString for SyncStatus {
    fn to_string(&self) -> String {
        match self {
            SyncStatus::Synced => "synced".to_string(),
            SyncStatus::Pending => "pending".to_string(),
            SyncStatus::Conflict => "conflict".to_string(),
        }
    }
}

/// 用户
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: String,
    pub email: Option<String>,
    pub phone: Option<String>,
    pub username: Option<String>,
    pub nickname: Option<String>,
    pub avatar: Option<String>,
    pub status: i64,
    pub is_superuser: bool,
    pub is_staff: bool,
    pub subscription_tier: String,
    pub settings: Option<String>,
    pub synced_at: Option<i64>,
    pub server_version: i64,
    pub created_at: i64,
    pub updated_at: i64,
}

/// 项目
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Project {
    pub id: String,
    pub user_id: String,
    pub name: String,
    pub description: Option<String>,
    pub industry: Option<String>,
    pub sub_industries: Option<String>,
    pub brand_name: Option<String>,
    pub brand_tone: Option<String>,
    pub brand_keywords: Option<String>,
    pub topics: Option<String>,
    pub keywords: Option<String>,
    pub account_tags: Option<String>,
    pub preferred_platforms: Option<String>,
    pub content_style: Option<String>,
    pub settings: Option<String>,
    pub is_default: bool,
    pub is_deleted: bool,
    pub deleted_at: Option<i64>,
    pub synced_at: Option<i64>,
    pub server_version: i64,
    pub local_version: i64,
    pub sync_status: String,
    pub created_at: i64,
    pub updated_at: i64,
}

/// 平台账号
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlatformAccount {
    pub id: String,
    pub user_id: String,
    pub project_id: String,
    pub platform: String,
    pub account_id: String,
    pub account_name: Option<String>,
    pub avatar_url: Option<String>,
    pub is_active: bool,
    pub session_valid: bool,
    pub last_session_check: Option<i64>,
    pub followers_count: i64,
    pub following_count: i64,
    pub posts_count: i64,
    pub metadata: Option<String>,
    pub last_profile_sync_at: Option<i64>,
    pub is_deleted: bool,
    pub deleted_at: Option<i64>,
    pub synced_at: Option<i64>,
    pub server_version: i64,
    pub local_version: i64,
    pub sync_status: String,
    pub created_at: i64,
    pub updated_at: i64,
}

/// 项目私有选题
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectTopic {
    pub id: String,
    pub user_id: String,
    pub project_id: String,
    pub title: String,
    pub payload: String,
    pub batch_date: Option<String>,
    pub source_uid: Option<String>,
    pub status: i64,
    pub is_deleted: bool,
    pub deleted_at: Option<i64>,
    pub synced_at: Option<i64>,
    pub server_version: i64,
    pub local_version: i64,
    pub sync_status: String,
    pub created_at: i64,
    pub updated_at: i64,
}

/// 内容
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Content {
    pub id: String,
    pub user_id: String,
    pub project_id: String,
    pub title: Option<String>,
    pub content_type: String,
    pub status: String,
    pub text_content: Option<String>,
    pub summary: Option<String>,
    pub media_urls: Option<String>,
    pub cover_url: Option<String>,
    pub tags: Option<String>,
    pub keywords: Option<String>,
    pub word_count: i64,
    pub read_time_minutes: i64,
    pub ai_generated: bool,
    pub generation_params: Option<String>,
    pub version: i64,
    pub parent_id: Option<String>,
    pub is_deleted: bool,
    pub deleted_at: Option<i64>,
    pub synced_at: Option<i64>,
    pub server_version: i64,
    pub local_version: i64,
    pub sync_status: String,
    pub created_at: i64,
    pub updated_at: i64,
}

/// 发布任务
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Publication {
    pub id: String,
    pub user_id: String,
    pub content_id: String,
    pub account_id: String,
    pub platform: String,
    pub status: String,
    pub adapted_content: Option<String>,
    pub scheduled_at: Option<i64>,
    pub published_at: Option<i64>,
    pub platform_post_id: Option<String>,
    pub platform_post_url: Option<String>,
    pub error_message: Option<String>,
    pub retry_count: i64,
    pub last_retry_at: Option<i64>,
    pub synced_at: Option<i64>,
    pub server_version: i64,
    pub local_version: i64,
    pub sync_status: String,
    pub created_at: i64,
    pub updated_at: i64,
}

/// 创建项目请求
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateProject {
    pub name: String,
    pub description: Option<String>,
    pub industry: Option<String>,
    pub sub_industries: Option<Vec<String>>,
    pub brand_name: Option<String>,
    pub brand_tone: Option<String>,
    pub brand_keywords: Option<Vec<String>>,
    pub topics: Option<Vec<String>>,
    pub keywords: Option<Vec<String>>,
}

/// 更新项目请求
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateProject {
    pub name: Option<String>,
    pub description: Option<String>,
    pub industry: Option<String>,
    pub sub_industries: Option<Vec<String>>,
    pub brand_name: Option<String>,
    pub brand_tone: Option<String>,
    pub brand_keywords: Option<Vec<String>>,
    pub topics: Option<Vec<String>>,
    pub keywords: Option<Vec<String>>,
    pub account_tags: Option<Vec<String>>,
    pub preferred_platforms: Option<Vec<String>>,
    pub content_style: Option<String>,
}

/// 创建内容请求
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateContent {
    pub project_id: String,
    pub title: Option<String>,
    pub content_type: String,
    pub text_content: Option<String>,
    pub tags: Option<Vec<String>>,
}

/// 创建发布任务请求
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreatePublication {
    pub content_id: String,
    pub account_id: String,
    pub platform: String,
    pub scheduled_at: Option<i64>,
}
