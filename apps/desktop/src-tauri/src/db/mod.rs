//! 数据库模块
//! @author Ysf

pub mod models;
pub mod repository;

pub use models::*;
pub use repository::Repository;

use std::path::PathBuf;
use std::sync::Mutex;
use tauri::AppHandle;

/// 数据库状态
pub struct DbState(pub Mutex<Option<Repository>>);

impl DbState {
    pub fn new() -> Self {
        Self(Mutex::new(None))
    }

    pub fn lock(&self) -> std::sync::LockResult<std::sync::MutexGuard<'_, Option<Repository>>> {
        self.0.lock()
    }
}

/// 获取数据库路径
/// 开发环境使用 ~/.ai-creator/ 目录
pub fn get_db_path(_app: &AppHandle) -> PathBuf {
    let home_dir = std::env::var("HOME").expect("Failed to get HOME environment variable");
    let data_dir = PathBuf::from(home_dir).join(".ai-creator");
    std::fs::create_dir_all(&data_dir).expect("Failed to create .ai-creator dir");
    data_dir.join("creatorflow.db")
}

/// 初始化数据库
pub fn init_db(app: &AppHandle) -> Result<Repository, String> {
    let db_path = get_db_path(app);
    let repo = Repository::open(&db_path).map_err(|e| format!("Failed to open database: {}", e))?;
    repo.init_schema().map_err(|e| format!("Failed to init schema: {}", e))?;
    Ok(repo)
}
