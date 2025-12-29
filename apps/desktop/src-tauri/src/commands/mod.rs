//! Tauri Commands 定义
//! @author Ysf

use serde::{Deserialize, Serialize};
use tauri::State;
use crate::SidecarState;
use crate::config::get_config;

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

// ============ 认证相关命令 ============

#[derive(Serialize, Deserialize)]
pub struct SendCodeRequest {
    pub phone: String,
}

#[derive(Serialize, Deserialize)]
pub struct PhoneLoginRequest {
    pub phone: String,
    pub code: String,
}

#[derive(Serialize, Deserialize)]
pub struct PasswordLoginRequest {
    pub username: String,
    pub password: String,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct UserInfo {
    pub id: i64,
    pub uuid: String,
    pub username: String,
    pub nickname: String,
    pub phone: Option<String>,
    pub email: Option<String>,
    pub avatar: Option<String>,
    pub is_new_user: bool,
}

#[derive(Serialize, Deserialize)]
pub struct LoginResponse {
    pub user: UserInfo,
    pub token: String,
    pub llm_token: String,
    pub is_new_user: bool,
}

/// 发送验证码
#[tauri::command]
pub async fn send_verification_code(phone: String) -> Result<String, String> {
    println!("[DEBUG] send_verification_code called with phone: {}", phone);

    let config = get_config();
    println!("[DEBUG] API endpoint: {}", config.endpoint("/auth/send-code"));

    let client = reqwest::Client::new();

    let resp = client
        .post(config.endpoint("/auth/send-code"))
        .json(&serde_json::json!({ "phone": phone }))
        .send()
        .await
        .map_err(|e| {
            println!("[DEBUG] Request error: {}", e);
            format!("网络请求失败: {}", e)
        })?;

    println!("[DEBUG] Response status: {}", resp.status());

    if !resp.status().is_success() {
        let error_text = resp.text().await.unwrap_or_else(|_| "未知错误".to_string());
        println!("[DEBUG] Error response: {}", error_text);
        return Err(format!("发送验证码失败: {}", error_text));
    }

    println!("[DEBUG] send_verification_code success");
    Ok("验证码已发送".to_string())
}

/// 手机号登录
#[tauri::command]
pub async fn phone_login(
    phone: String,
    code: String,
    state: State<'_, SidecarState>,
) -> Result<LoginResponse, String> {
    let config = get_config();
    let client = reqwest::Client::new();

    // 1. 调用云端手机号登录 API
    let resp = client
        .post(config.endpoint("/auth/phone-login"))
        .json(&serde_json::json!({
            "phone": phone,
            "code": code
        }))
        .send()
        .await
        .map_err(|e| format!("网络请求失败: {}", e))?;

    if !resp.status().is_success() {
        let error_text = resp.text().await.unwrap_or_else(|_| "未知错误".to_string());
        return Err(format!("登录失败: {}", error_text));
    }

    // 解析响应
    let resp_json: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| format!("解析响应失败: {}", e))?;

    // 提取数据
    let data = resp_json.get("data").ok_or("响应格式错误")?;

    let access_token = data
        .get("access_token")
        .and_then(|v| v.as_str())
        .ok_or("缺少 access_token")?
        .to_string();

    let llm_token = data
        .get("llm_token")
        .and_then(|v| v.as_str())
        .ok_or("缺少 llm_token")?
        .to_string();

    let access_token_expire_time = data
        .get("access_token_expire_time")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();

    let refresh_token = data
        .get("refresh_token")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();

    let refresh_token_expire_time = data
        .get("refresh_token_expire_time")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();

    let is_new_user = data
        .get("is_new_user")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);

    let user_data = data.get("user").ok_or("缺少用户信息")?;

    let user = UserInfo {
        id: user_data.get("id").and_then(|v| v.as_i64()).unwrap_or(0),
        uuid: user_data
            .get("uuid")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string(),
        username: user_data
            .get("username")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string(),
        nickname: user_data
            .get("nickname")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string(),
        phone: user_data
            .get("phone")
            .and_then(|v| v.as_str())
            .map(String::from),
        email: user_data
            .get("email")
            .and_then(|v| v.as_str())
            .map(String::from),
        avatar: user_data
            .get("avatar")
            .and_then(|v| v.as_str())
            .map(String::from),
        is_new_user,
    };

    // 2. 调用 Sidecar 保存 LLM Token 和 Access Token
    {
        let mut manager = state.0.lock().map_err(|e| e.to_string())?;
        if manager.is_running() {
            let _ = manager.call(
                "login",
                serde_json::json!({
                    "api_token": llm_token,
                    "access_token": access_token,
                    "access_token_expire_time": access_token_expire_time,
                    "refresh_token": refresh_token,
                    "refresh_token_expire_time": refresh_token_expire_time,
                    "environment": config.environment
                }),
            );
        }
    }

    Ok(LoginResponse {
        user,
        token: access_token,
        llm_token,
        is_new_user,
    })
}

/// 用户名密码登录
#[tauri::command]
pub async fn password_login(
    username: String,
    password: String,
    state: State<'_, SidecarState>,
) -> Result<LoginResponse, String> {
    let config = get_config();
    let client = reqwest::Client::new();

    // 1. 调用云端登录 API
    let resp = client
        .post(config.endpoint("/auth/login"))
        .json(&serde_json::json!({
            "username": username,
            "password": password
        }))
        .send()
        .await
        .map_err(|e| format!("网络请求失败: {}", e))?;

    if !resp.status().is_success() {
        let error_text = resp.text().await.unwrap_or_else(|_| "未知错误".to_string());
        return Err(format!("登录失败: {}", error_text));
    }

    // 解析响应
    let resp_json: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| format!("解析响应失败: {}", e))?;

    let data = resp_json.get("data").ok_or("响应格式错误")?;

    let access_token = data
        .get("access_token")
        .and_then(|v| v.as_str())
        .ok_or("缺少 access_token")?
        .to_string();

    let access_token_expire_time = data
        .get("access_token_expire_time")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();

    let refresh_token = data
        .get("refresh_token")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();

    let refresh_token_expire_time = data
        .get("refresh_token_expire_time")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();

    // 2. 获取 LLM Token
    let llm_resp = client
        .post(config.endpoint("/auth/llm-token"))
        .header("Authorization", format!("Bearer {}", access_token))
        .send()
        .await
        .map_err(|e| format!("获取 LLM Token 失败: {}", e))?;

    let llm_json: serde_json::Value = llm_resp
        .json()
        .await
        .map_err(|e| format!("解析 LLM Token 响应失败: {}", e))?;

    let llm_data = llm_json.get("data").ok_or("LLM Token 响应格式错误")?;
    let llm_token = llm_data
        .get("api_token")
        .and_then(|v| v.as_str())
        .ok_or("缺少 api_token")?
        .to_string();

    // 提取用户信息
    let user_data = data.get("user").ok_or("缺少用户信息")?;

    let user = UserInfo {
        id: user_data.get("id").and_then(|v| v.as_i64()).unwrap_or(0),
        uuid: user_data
            .get("uuid")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string(),
        username: user_data
            .get("username")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string(),
        nickname: user_data
            .get("nickname")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string(),
        phone: user_data
            .get("phone")
            .and_then(|v| v.as_str())
            .map(String::from),
        email: user_data
            .get("email")
            .and_then(|v| v.as_str())
            .map(String::from),
        avatar: user_data
            .get("avatar")
            .and_then(|v| v.as_str())
            .map(String::from),
        is_new_user: false,
    };

    // 3. 调用 Sidecar 保存 LLM Token 和 Access Token
    {
        let mut manager = state.0.lock().map_err(|e| e.to_string())?;
        if manager.is_running() {
            let _ = manager.call(
                "login",
                serde_json::json!({
                    "api_token": llm_token,
                    "access_token": access_token,
                    "access_token_expire_time": access_token_expire_time,
                    "refresh_token": refresh_token,
                    "refresh_token_expire_time": refresh_token_expire_time,
                    "environment": config.environment
                }),
            );
        }
    }

    Ok(LoginResponse {
        user,
        token: access_token,
        llm_token,
        is_new_user: false,
    })
}

/// 用户登出
#[tauri::command]
pub async fn logout(state: State<'_, SidecarState>) -> Result<String, String> {
    let config = get_config();

    // 调用 Sidecar 清除 LLM Token
    {
        let mut manager = state.0.lock().map_err(|e| e.to_string())?;
        if manager.is_running() {
            let _ = manager.call(
                "logout",
                serde_json::json!({
                    "environment": config.environment
                }),
            );
        }
    }

    Ok("已登出".to_string())
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
            // 检查执行是否成功
            let success = result.get("success")
                .and_then(|v| v.as_bool())
                .unwrap_or(false);

            if !success {
                let error = result.get("error")
                    .and_then(|v| v.as_str())
                    .unwrap_or("执行失败")
                    .to_string();
                return Ok(AIWritingResponse {
                    success: false,
                    data: None,
                    error: Some(error),
                });
            }

            // 解析 outputs 字段
            if let Some(outputs) = result.get("outputs") {
                // 尝试从 outputs 中提取 title, content, tags
                // Graph 返回的是 final_content, outline 等字段
                let content = outputs.get("final_content")
                    .or_else(|| outputs.get("content"))
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string();

                let title = outputs.get("title")
                    .and_then(|v| v.as_str())
                    .unwrap_or("")
                    .to_string();

                let tags = outputs.get("tags")
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
