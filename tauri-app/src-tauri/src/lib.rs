//! 创流桌面端 Tauri 后端库
//! @author Ysf

use tauri::Manager;
use std::sync::Mutex;

mod commands;
mod sidecar;

use sidecar::SidecarManager;

/// 全局 Sidecar 管理器状态
pub struct SidecarState(pub Mutex<SidecarManager>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(SidecarState(Mutex::new(SidecarManager::new())))
        .invoke_handler(tauri::generate_handler![
            commands::greet,
            commands::get_app_info,
            commands::execute_ai_writing,
            commands::init_sidecar,
            commands::shutdown_sidecar,
            commands::sidecar_health_check,
        ])
        .setup(|app| {
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
