//! Tauri Commands 定义
//! @author Ysf

use serde::{Deserialize, Serialize};
use tauri::State;
use crate::SidecarState;

#[derive(Serialize, Deserialize)]
pub struct AppInfo {
    pub name: String,
    pub version: String,
    pub description: String,
}

/// 问候命令
#[tauri::command]
pub fn greet(name: &str) -> String {
    format!("你好, {}! 欢迎使用创流桌面端!", name)
}

/// 获取应用信息
#[tauri::command]
pub fn get_app_info() -> AppInfo {
    AppInfo {
        name: "创流".to_string(),
        version: "0.1.0".to_string(),
        description: "自媒体创作者的 AI 超级大脑".to_string(),
    }
}

// ============ Sidecar 管理命令 ============

/// 初始化 Sidecar
#[tauri::command]
pub fn init_sidecar(
    sidecar_path: String,
    state: State<SidecarState>,
) -> Result<String, String> {
    let mut manager = state.0.lock().map_err(|e| e.to_string())?;
    manager.spawn(&sidecar_path)?;
    Ok("Sidecar 启动成功".to_string())
}

/// 关闭 Sidecar
#[tauri::command]
pub fn shutdown_sidecar(state: State<SidecarState>) -> Result<String, String> {
    let mut manager = state.0.lock().map_err(|e| e.to_string())?;
    manager.shutdown()?;
    Ok("Sidecar 已关闭".to_string())
}

/// Sidecar 健康检查
#[tauri::command]
pub fn sidecar_health_check(state: State<SidecarState>) -> Result<bool, String> {
    let mut manager = state.0.lock().map_err(|e| e.to_string())?;
    manager.health_check()
}

// ============ AI 写作相关命令 ============

#[derive(Serialize, Deserialize)]
pub struct AIWritingRequest {
    pub graph_name: String,
    pub inputs: serde_json::Value,
    pub user_id: String,
}

#[derive(Serialize, Deserialize)]
pub struct AIWritingResult {
    pub title: String,
    pub content: String,
    pub tags: Vec<String>,
}

#[derive(Serialize, Deserialize)]
pub struct AIWritingResponse {
    pub success: bool,
    pub data: Option<AIWritingResult>,
    pub error: Option<String>,
}

/// 执行 AI 写作
#[tauri::command]
pub async fn execute_ai_writing(
    request: AIWritingRequest,
    state: State<'_, SidecarState>,
) -> Result<AIWritingResponse, String> {
    // 获取 Sidecar 管理器
    let mut manager = state.0.lock().map_err(|e| e.to_string())?;

    // 检查 Sidecar 是否运行
    if !manager.is_running() {
        return Ok(AIWritingResponse {
            success: false,
            data: None,
            error: Some("Sidecar 未启动，请先初始化".to_string()),
        });
    }

    // 调用 Sidecar 执行 Graph
    let params = serde_json::json!({
        "graph_name": request.graph_name,
        "inputs": request.inputs,
        "user_id": request.user_id,
    });

    match manager.call("execute_graph", params) {
        Ok(result) => {
            // 解析结果
            if let Some(data) = result.get("data") {
                let title = data.get("title")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string();
                let content = data.get("content")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string();
                let tags = data.get("tags")
                    .and_then(|v| v.as_array())
                    .map(|arr| arr.iter()
                        .filter_map(|v| v.as_str().map(String::from))
                        .collect())
                    .unwrap_or_default();

                Ok(AIWritingResponse {
                    success: true,
                    data: Some(AIWritingResult { title, content, tags }),
                    error: None,
                })
            } else {
                Ok(AIWritingResponse {
                    success: false,
                    data: None,
                    error: Some("执行结果为空".to_string()),
                })
            }
        }
        Err(e) => Ok(AIWritingResponse {
            success: false,
            data: None,
            error: Some(e),
        }),
    }
}
