//! 数据库模块
//! @author Ysf

pub mod models;
pub mod repository;

pub use models::*;
pub use repository::Repository;

use std::path::PathBuf;
use std::sync::Mutex;
use tauri::{AppHandle, Manager};

/// 数据库状态
pub struct DbState(pub Mutex<Option<Repository>>);

impl DbState {
    pub fn new() -> Self {
        Self(Mutex::new(None))
    }
}

/// 获取数据库路径
pub fn get_db_path(app: &AppHandle) -> PathBuf {
    let app_data_dir = app.path().app_data_dir().expect("Failed to get app data dir");
    std::fs::create_dir_all(&app_data_dir).expect("Failed to create app data dir");
    app_data_dir.join("creatorflow.db")
}

/// 初始化数据库
pub fn init_db(app: &AppHandle) -> Result<Repository, String> {
    let db_path = get_db_path(app);
    let repo = Repository::open(&db_path).map_err(|e| format!("Failed to open database: {}", e))?;
    repo.init_schema().map_err(|e| format!("Failed to init schema: {}", e))?;
    Ok(repo)
}
