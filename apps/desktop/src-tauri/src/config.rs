//! API 配置管理
//! @author Ysf

use std::sync::OnceLock;

/// API 配置
#[derive(Debug, Clone)]
pub struct ApiConfig {
    /// API 基础 URL
    pub base_url: String,
    /// 环境 (development/production)
    pub environment: String,
}

impl ApiConfig {
    /// 从环境变量加载配置
    pub fn load() -> Self {
        let env = std::env::var("APP_ENV").unwrap_or_else(|_| "development".to_string());
        let base_url = match env.as_str() {
            "production" => "https://api.ai-creator.com".to_string(),
            _ => "http://localhost:8010".to_string(),
        };

        Self {
            base_url,
            environment: env,
        }
    }

    /// 获取 API 端点 URL
    pub fn endpoint(&self, path: &str) -> String {
        format!("{}/api/v1{}", self.base_url, path)
    }
}

impl Default for ApiConfig {
    fn default() -> Self {
        Self::load()
    }
}

/// 全局配置实例
static CONFIG: OnceLock<ApiConfig> = OnceLock::new();

/// 获取全局配置
pub fn get_config() -> &'static ApiConfig {
    CONFIG.get_or_init(ApiConfig::load)
}

/// API 配置状态 (用于 Tauri State)
pub struct ApiConfigState(pub ApiConfig);
