//! 同步引擎
//! 负责调度和执行同步任务

use std::sync::{Arc, Mutex};
use crate::db::Repository;
use super::api_client::ApiClient;
use super::providers::SyncProvider;

/// 同步状态
#[derive(Debug, Clone, serde::Serialize)]
pub struct SyncStatus {
    pub is_syncing: bool,
    pub last_sync_time: Option<i64>,
    pub last_error: Option<String>,
}

/// 同步引擎
pub struct SyncEngine {
    repo: Arc<Repository>,
    client: ApiClient,
    providers: Vec<Box<dyn SyncProvider>>,
    status: Arc<Mutex<SyncStatus>>,
}

impl SyncEngine {
    pub fn new(repo: Arc<Repository>) -> Self {
        Self {
            repo,
            client: ApiClient::new(),
            providers: Vec::new(),
            status: Arc::new(Mutex::new(SyncStatus {
                is_syncing: false,
                last_sync_time: None,
                last_error: None,
            })),
        }
    }

    /// 注册同步提供者
    pub fn register_provider<P: SyncProvider + 'static>(&mut self, provider: P) {
        self.providers.push(Box::new(provider));
    }

    /// 获取当前状态
    pub fn get_status(&self) -> SyncStatus {
        self.status.lock().unwrap().clone()
    }

    /// 开始同步 (异步执行)
    pub async fn start_sync(&self, user_id: String, token: String) -> Result<(), String> {
        // 更新状态为正在同步
        {
            let mut status = self.status.lock().unwrap();
            if status.is_syncing {
                return Ok(()); // 已经在同步中，忽略
            }
            status.is_syncing = true;
            status.last_error = None;
        }

        println!("[SyncEngine] Start syncing for user: {}", user_id);

        let mut final_result = Ok(());

        // 遍历所有提供者执行同步
        for provider in &self.providers {
            println!("[SyncEngine] Syncing provider: {}", provider.name());
            
            // 1. Pull
            if let Err(e) = provider.pull(&self.client, &self.repo, &user_id, &token).await {
                let err_msg = format!("Pull failed for {}: {}", provider.name(), e);
                eprintln!("[SyncEngine] {}", err_msg);
                final_result = Err(err_msg.clone());
                // 继续执行其他 provider，不中断
            }

            // 2. Push
            if let Err(e) = provider.push(&self.client, &self.repo, &user_id, &token).await {
                let err_msg = format!("Push failed for {}: {}", provider.name(), e);
                eprintln!("[SyncEngine] {}", err_msg);
                if final_result.is_ok() {
                    final_result = Err(err_msg);
                }
            }
        }

        // 更新状态
        {
            let mut status = self.status.lock().unwrap();
            status.is_syncing = false;
            if final_result.is_ok() {
                status.last_sync_time = Some(chrono::Utc::now().timestamp());
                println!("[SyncEngine] Sync completed successfully");
            } else {
                status.last_error = final_result.clone().err();
                println!("[SyncEngine] Sync completed with errors");
            }
        }

        final_result
    }
}
