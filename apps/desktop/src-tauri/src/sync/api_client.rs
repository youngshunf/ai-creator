//! API 客户端
//! 封装 reqwest 请求，处理认证和错误

use reqwest::Client;
use serde::de::DeserializeOwned;
use serde::Serialize;
use std::time::Duration;
use crate::config::get_config;

pub struct ApiClient {
    client: Client,
}

impl ApiClient {
    pub fn new() -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(30))
            .build()
            .unwrap_or_default();
        Self { client }
    }

    /// 发送 GET 请求
    pub async fn get<T: DeserializeOwned>(&self, path: &str, token: Option<&str>) -> Result<T, String> {
        let config = get_config();
        let url = config.endpoint(path);
        
        let mut builder = self.client.get(&url);
        if let Some(t) = token {
            builder = builder.header("Authorization", format!("Bearer {}", t));
        }

        let resp = builder
            .send()
            .await
            .map_err(|e| format!("Network error: {}", e))?;

        if !resp.status().is_success() {
            let status = resp.status();
            let text = resp.text().await.unwrap_or_default();
            return Err(format!("API error {}: {}", status, text));
        }

        // 先读取文本，以便在解析失败时记录日志
        let text = resp.text().await.map_err(|e| format!("Failed to read response body: {}", e))?;
        serde_json::from_str::<T>(&text)
            .map_err(|e| format!("Parse error: {} Body: {}", e, text))
    }

    /// 发送 POST 请求
    pub async fn post<T: DeserializeOwned, B: Serialize + ?Sized>(&self, path: &str, body: &B, token: Option<&str>) -> Result<T, String> {
        let config = get_config();
        let url = config.endpoint(path);

        let mut builder = self.client.post(&url);
        if let Some(t) = token {
            builder = builder.header("Authorization", format!("Bearer {}", t));
        }

        let resp = builder
            .json(body)
            .send()
            .await
            .map_err(|e| format!("Network error: {}", e))?;

        if !resp.status().is_success() {
            let status = resp.status();
            let text = resp.text().await.unwrap_or_default();
            return Err(format!("API error {}: {}", status, text));
        }

        let text = resp.text().await.map_err(|e| format!("Failed to read response body: {}", e))?;
        serde_json::from_str::<T>(&text)
            .map_err(|e| format!("Parse error: {} Body: {}", e, text))
    }

    /// 发送 PUT 请求
    pub async fn put<T: DeserializeOwned, B: Serialize + ?Sized>(&self, path: &str, body: &B, token: Option<&str>) -> Result<T, String> {
        let config = get_config();
        let url = config.endpoint(path);

        let mut builder = self.client.put(&url);
        if let Some(t) = token {
            builder = builder.header("Authorization", format!("Bearer {}", t));
        }

        let resp = builder
            .json(body)
            .send()
            .await
            .map_err(|e| format!("Network error: {}", e))?;

        if !resp.status().is_success() {
            let status = resp.status();
            let text = resp.text().await.unwrap_or_default();
            return Err(format!("API error {}: {}", status, text));
        }

        let text = resp.text().await.map_err(|e| format!("Failed to read response body: {}", e))?;
        serde_json::from_str::<T>(&text)
            .map_err(|e| format!("Parse error: {} Body: {}", e, text))
    }
}
