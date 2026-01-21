//! 创流桌面端 Tauri 后端库
//! @author Ysf

use tauri::Manager;
// use std::sync::Mutex; // Remove this duplicate import or let rustc warn

mod commands;
mod config;
mod db;
mod sidecar;
mod sync;

use db::{DbState, init_db};
use sidecar::SidecarManager;
use sync::{SyncEngine, providers::{UserProvider, ProjectProvider, AccountProvider}};
use std::sync::{Arc, Mutex};

/// 全局 Sidecar 管理器状态
pub struct SidecarState(pub Mutex<SidecarManager>);

impl SidecarState {
    pub fn lock(&self) -> std::sync::LockResult<std::sync::MutexGuard<'_, SidecarManager>> {
        self.0.lock()
    }
}

/// 全局同步引擎状态
pub struct SyncState(pub Mutex<Option<Arc<SyncEngine>>>);

impl SyncState {
    pub fn lock(&self) -> std::sync::LockResult<std::sync::MutexGuard<'_, Option<Arc<SyncEngine>>>> {
        self.0.lock()
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(SidecarState(Mutex::new(SidecarManager::new())))
        .manage(DbState::new())
        .manage(SyncState(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![
            commands::greet,
            commands::get_app_info,
            commands::execute_ai_writing,
            commands::init_sidecar,
            commands::shutdown_sidecar,
            commands::sidecar_health_check,
            commands::send_verification_code,
            commands::phone_login,
            commands::password_login,
            commands::logout,
            commands::sync_auth_tokens,
            // 项目管理命令
            commands::get_projects,
            commands::create_project,
            commands::update_project,
            commands::delete_project,
            commands::set_default_project,
            // LLM 状态命令
            commands::check_llm_connection,
            commands::get_available_models,
            commands::get_usage_stats,
            // 数据库命令
            commands::db_init,
            commands::db_list_projects,
            commands::db_create_project,
            commands::db_delete_project,
            commands::db_set_default_project,
            commands::db_list_contents,
            commands::db_create_content,
            commands::db_update_content,
            commands::db_delete_content,
            commands::db_list_accounts,
            commands::db_create_account,
            commands::db_delete_account,
            commands::db_list_publications,
            commands::db_create_publication,
            commands::db_update_publication_status,
            commands::sync_user_to_local,
            commands::sync_project_to_local,
            commands::start_platform_login,
            commands::check_platform_login_status,
            commands::close_login_browser,
            // 账号同步命令
            commands::sync_account,
            commands::sync_all_accounts,
            commands::db_update_account_profile,
            // 同步服务命令
            commands::start_sync,
            commands::get_sync_status,
        ])
        .setup(|app| {
            // 初始化数据库
            match init_db(&app.handle()) {
                Ok(repo) => {
                    // 1. 初始化 DbState
                    let db_state = app.state::<DbState>();
                    *db_state.lock().unwrap() = Some(repo.clone());
                    println!("[DB] Database initialized successfully");

                    // 2. 初始化 SyncEngine
                    // 这里我们创建一个 Arc<Repository> 用于共享
                    let repo_arc = Arc::new(repo);
                    let mut engine = SyncEngine::new(repo_arc);
                    
                    // 注册提供者 (顺序很重要：先同步用户，再同步依赖用户的实体)
                    engine.register_provider(UserProvider);
                    engine.register_provider(ProjectProvider);
                    engine.register_provider(AccountProvider);
                    
                    let sync_state = app.state::<SyncState>();
                    *sync_state.lock().unwrap() = Some(Arc::new(engine));
                    println!("[Sync] SyncEngine initialized successfully");
                }
                Err(e) => {
                    eprintln!("[DB] Failed to initialize database: {}", e);
                }
            }

            #[cfg(debug_assertions)]
            {
                let window = app.get_webview_window("main").unwrap();
                window.open_devtools();
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
