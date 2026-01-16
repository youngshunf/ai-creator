//! Tauri Commands 定义
//! @author Ysf

use serde::{Deserialize, Serialize};
use tauri::{State, AppHandle, Emitter};
use crate::{SidecarState, SyncState};
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
    db_state: State<'_, DbState>,
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
        let mut manager = state.lock().map_err(|e| e.to_string())?;
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

    // 3. 同步用户到本地数据库
    {
        if let Ok(guard) = db_state.lock() {
            if let Some(repo) = guard.as_ref() {
                let _ = repo.sync_user(
                    &user.id.to_string(),
                    user.email.as_deref(),
                    Some(&user.username),
                    Some(&user.nickname),
                    user.avatar.as_deref()
                );
            }
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
    db_state: State<'_, DbState>,
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
        let mut manager = state.lock().map_err(|e| e.to_string())?;
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

    // 4. 同步用户到本地数据库
    {
        if let Ok(guard) = db_state.lock() {
            if let Some(repo) = guard.as_ref() {
                let _ = repo.sync_user(
                    &user.id.to_string(),
                    user.email.as_deref(),
                    Some(&user.username),
                    Some(&user.nickname),
                    user.avatar.as_deref()
                );
            }
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
        let mut manager = state.lock().map_err(|e| e.to_string())?;
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

// ============ Token 同步命令 ============

#[derive(Serialize, Deserialize)]
pub struct SyncAuthTokensRequest {
    pub api_token: Option<String>,
    pub access_token: String,
    pub access_token_expire_time: Option<String>,
    pub refresh_token: Option<String>,
    pub refresh_token_expire_time: Option<String>,
}

/// 同步前端 Token 到 Sidecar
/// 前端通过 Axios 登录后调用此命令，将 Token 同步到本地配置文件
#[tauri::command]
pub async fn sync_auth_tokens(
    request: SyncAuthTokensRequest,
    state: State<'_, SidecarState>,
) -> Result<String, String> {
    let config = get_config();
    
    // 调用 Sidecar 同步 Token
    {
        let mut manager = state.lock().map_err(|e| e.to_string())?;
        if manager.is_running() {
            let result = manager.call(
                "sync_auth_tokens",
                serde_json::json!({
                    "api_token": request.api_token.unwrap_or_default(),
                    "access_token": request.access_token,
                    "access_token_expire_time": request.access_token_expire_time.unwrap_or_default(),
                    "refresh_token": request.refresh_token.unwrap_or_default(),
                    "refresh_token_expire_time": request.refresh_token_expire_time.unwrap_or_default(),
                    "environment": config.environment
                }),
            );
            
            match result {
                Ok(_) => Ok("Token 同步成功".to_string()),
                Err(e) => Err(format!("Token 同步失败: {}", e)),
            }
        } else {
            Err("Sidecar 未运行".to_string())
        }
    }
}

// ============ Sidecar 管理命令 ============

/// 初始化 Sidecar
#[tauri::command]
pub fn init_sidecar(
    sidecar_path: String,
    state: State<SidecarState>,
) -> Result<String, String> {
    let mut manager = state.lock().map_err(|e| e.to_string())?;
    manager.spawn(&sidecar_path)?;
    Ok("Sidecar 启动成功".to_string())
}

/// 关闭 Sidecar
#[tauri::command]
pub fn shutdown_sidecar(state: State<SidecarState>) -> Result<String, String> {
    let mut manager = state.lock().map_err(|e| e.to_string())?;
    manager.shutdown()?;
    Ok("Sidecar 已关闭".to_string())
}

/// Sidecar 健康检查
#[tauri::command]
pub fn sidecar_health_check(state: State<SidecarState>) -> Result<bool, String> {
    let mut manager = state.lock().map_err(|e| e.to_string())?;
    manager.health_check()
}

// ============ AI 写作相关命令 ============

#[derive(Serialize, Deserialize)]
pub struct AIWritingRequest {
    pub graph_name: String,
    pub inputs: serde_json::Value,
    pub user_id: String,
    pub access_token: String,
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
    let mut manager = state.lock().map_err(|e| e.to_string())?;

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
        "access_token": request.access_token,
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

// ============ 项目管理相关命令 ============

#[derive(Serialize, Deserialize, Clone)]
pub struct ProjectCreate {
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

#[derive(Serialize, Deserialize, Clone)]
pub struct ProjectUpdate {
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

/// 获取项目列表
#[tauri::command]
pub async fn get_projects() -> Result<serde_json::Value, String> {
    let config = get_config();
    let client = reqwest::Client::new();

    let resp = client
        .get(config.endpoint("/projects"))
        .send()
        .await
        .map_err(|e| format!("网络请求失败: {}", e))?;

    if !resp.status().is_success() {
        let error_text = resp.text().await.unwrap_or_else(|_| "未知错误".to_string());
        return Err(format!("获取项目列表失败: {}", error_text));
    }

    resp.json()
        .await
        .map_err(|e| format!("解析响应失败: {}", e))
}

/// 创建项目
#[tauri::command]
pub async fn create_project(data: ProjectCreate) -> Result<serde_json::Value, String> {
    let config = get_config();
    let client = reqwest::Client::new();

    let resp = client
        .post(config.endpoint("/projects"))
        .json(&data)
        .send()
        .await
        .map_err(|e| format!("网络请求失败: {}", e))?;

    if !resp.status().is_success() {
        let error_text = resp.text().await.unwrap_or_else(|_| "未知错误".to_string());
        return Err(format!("创建项目失败: {}", error_text));
    }

    resp.json()
        .await
        .map_err(|e| format!("解析响应失败: {}", e))
}

/// 更新项目
#[tauri::command]
pub async fn update_project(id: i64, data: ProjectUpdate) -> Result<serde_json::Value, String> {
    let config = get_config();
    let client = reqwest::Client::new();

    let resp = client
        .put(config.endpoint(&format!("/projects/{}", id)))
        .json(&data)
        .send()
        .await
        .map_err(|e| format!("网络请求失败: {}", e))?;

    if !resp.status().is_success() {
        let error_text = resp.text().await.unwrap_or_else(|_| "未知错误".to_string());
        return Err(format!("更新项目失败: {}", error_text));
    }

    resp.json()
        .await
        .map_err(|e| format!("解析响应失败: {}", e))
}

/// 删除项目
#[tauri::command]
pub async fn delete_project(id: i64) -> Result<serde_json::Value, String> {
    let config = get_config();
    let client = reqwest::Client::new();

    let resp = client
        .delete(config.endpoint(&format!("/projects/{}", id)))
        .send()
        .await
        .map_err(|e| format!("网络请求失败: {}", e))?;

    if !resp.status().is_success() {
        let error_text = resp.text().await.unwrap_or_else(|_| "未知错误".to_string());
        return Err(format!("删除项目失败: {}", error_text));
    }

    resp.json()
        .await
        .map_err(|e| format!("解析响应失败: {}", e))
}

/// 设置默认项目
#[tauri::command]
pub async fn set_default_project(id: i64) -> Result<serde_json::Value, String> {
    let config = get_config();
    let client = reqwest::Client::new();

    let resp = client
        .post(config.endpoint(&format!("/projects/{}/set-default", id)))
        .send()
        .await
        .map_err(|e| format!("网络请求失败: {}", e))?;

    if !resp.status().is_success() {
        let error_text = resp.text().await.unwrap_or_else(|_| "未知错误".to_string());
        return Err(format!("设置默认项目失败: {}", error_text));
    }

    resp.json()
        .await
        .map_err(|e| format!("解析响应失败: {}", e))
}

// ============ LLM 状态相关命令 ============

#[derive(Serialize, Deserialize)]
pub struct ModelInfo {
    #[serde(rename = "modelId")]
    pub model_id: String,
    pub provider: String,
    #[serde(rename = "displayName")]
    pub display_name: String,
    #[serde(rename = "maxTokens")]
    pub max_tokens: i32,
    #[serde(rename = "supportsStreaming")]
    pub supports_streaming: bool,
    #[serde(rename = "supportsVision")]
    pub supports_vision: bool,
}

#[derive(Serialize, Deserialize)]
pub struct UsageStats {
    #[serde(rename = "totalTokens")]
    pub total_tokens: i64,
    #[serde(rename = "totalCost")]
    pub total_cost: f64,
    #[serde(rename = "requestCount")]
    pub request_count: i64,
    pub period: String,
}

/// 检查 LLM 连接状态
#[tauri::command]
pub async fn check_llm_connection() -> Result<serde_json::Value, String> {
    let config = get_config();
    let client = reqwest::Client::new();

    // 尝试调用健康检查端点
    let resp = client
        .get(config.endpoint("/v1/llm/health"))
        .timeout(std::time::Duration::from_secs(5))
        .send()
        .await;

    match resp {
        Ok(r) if r.status().is_success() => {
            Ok(serde_json::json!({
                "success": true
            }))
        }
        Ok(r) => {
            Ok(serde_json::json!({
                "success": false,
                "error": format!("服务返回错误状态: {}", r.status())
            }))
        }
        Err(e) => {
            Ok(serde_json::json!({
                "success": false,
                "error": format!("无法连接到 LLM 服务: {}", e)
            }))
        }
    }
}

/// 获取可用模型列表
#[tauri::command]
pub async fn get_available_models() -> Result<serde_json::Value, String> {
    // 返回预定义的模型列表（后续可从后端 API 获取）
    let models = vec![
        ModelInfo {
            model_id: "claude-3-5-sonnet".to_string(),
            provider: "anthropic".to_string(),
            display_name: "Claude 3.5 Sonnet".to_string(),
            max_tokens: 200000,
            supports_streaming: true,
            supports_vision: true,
        },
        ModelInfo {
            model_id: "gpt-4o".to_string(),
            provider: "openai".to_string(),
            display_name: "GPT-4o".to_string(),
            max_tokens: 128000,
            supports_streaming: true,
            supports_vision: true,
        },
        ModelInfo {
            model_id: "gpt-4o-mini".to_string(),
            provider: "openai".to_string(),
            display_name: "GPT-4o Mini".to_string(),
            max_tokens: 128000,
            supports_streaming: true,
            supports_vision: true,
        },
        ModelInfo {
            model_id: "deepseek-chat".to_string(),
            provider: "deepseek".to_string(),
            display_name: "DeepSeek Chat".to_string(),
            max_tokens: 64000,
            supports_streaming: true,
            supports_vision: false,
        },
    ];

    Ok(serde_json::json!({
        "success": true,
        "data": models
    }))
}

/// 获取用量统计
#[tauri::command]
pub async fn get_usage_stats(period: String) -> Result<serde_json::Value, String> {
    // 返回模拟数据（后续可从后端 API 获取真实数据）
    let stats = UsageStats {
        total_tokens: 125000,
        total_cost: 2.50,
        request_count: 42,
        period,
    };

    Ok(serde_json::json!({
        "success": true,
        "data": stats
    }))
}

// ============ 本地数据库命令 ============

use crate::db::{DbState, CreateProject as DbCreateProject, CreateContent as DbCreateContent, CreatePublication as DbCreatePublication};

/// 初始化数据库
#[tauri::command]
pub fn db_init(state: State<DbState>) -> Result<String, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    if db.is_some() {
        Ok("数据库已初始化".to_string())
    } else {
        Err("数据库未初始化".to_string())
    }
}

/// 获取本地项目列表
#[tauri::command]
pub fn db_list_projects(user_id: String, state: State<DbState>) -> Result<serde_json::Value, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    let projects = repo.list_projects(&user_id).map_err(|e| e.to_string())?;
    Ok(serde_json::to_value(projects).unwrap())
}

/// 创建本地项目
#[tauri::command]
pub fn db_create_project(user_id: String, data: DbCreateProject, state: State<DbState>) -> Result<serde_json::Value, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    let project = repo.create_project(&user_id, &data).map_err(|e| e.to_string())?;
    Ok(serde_json::to_value(project).unwrap())
}

/// 删除本地项目
#[tauri::command]
pub fn db_delete_project(id: String, state: State<DbState>) -> Result<String, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    repo.delete_project(&id).map_err(|e| e.to_string())?;
    Ok("删除成功".to_string())
}

/// 获取本地内容列表
#[tauri::command]
pub fn db_list_contents(project_id: String, state: State<DbState>) -> Result<serde_json::Value, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    let contents = repo.list_contents(&project_id).map_err(|e| e.to_string())?;
    Ok(serde_json::to_value(contents).unwrap())
}

/// 创建本地内容
#[tauri::command]
pub fn db_create_content(user_id: String, data: DbCreateContent, state: State<DbState>) -> Result<serde_json::Value, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    let content = repo.create_content(&user_id, &data).map_err(|e| e.to_string())?;
    Ok(serde_json::to_value(content).unwrap())
}

/// 更新本地内容
#[tauri::command]
pub fn db_update_content(id: String, title: Option<String>, text_content: Option<String>, state: State<DbState>) -> Result<String, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    repo.update_content(&id, title.as_deref(), text_content.as_deref()).map_err(|e| e.to_string())?;
    Ok("更新成功".to_string())
}

/// 删除本地内容
#[tauri::command]
pub fn db_delete_content(id: String, state: State<DbState>) -> Result<String, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    repo.delete_content(&id).map_err(|e| e.to_string())?;
    Ok("删除成功".to_string())
}

/// 获取本地平台账号列表
#[tauri::command]
pub fn db_list_accounts(project_id: String, state: State<DbState>) -> Result<serde_json::Value, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    let accounts = repo.list_platform_accounts(&project_id).map_err(|e| e.to_string())?;
    Ok(serde_json::to_value(accounts).unwrap())
}

/// 创建本地平台账号
#[tauri::command]
pub fn db_create_account(user_id: String, project_id: String, platform: String, account_id: String, account_name: Option<String>, state: State<DbState>) -> Result<serde_json::Value, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    // 确保项目存在（满足外键约束）
    repo.ensure_project_exists(&project_id, &user_id).map_err(|e| e.to_string())?;
    let account = repo.create_platform_account(&user_id, &project_id, &platform, &account_id, account_name.as_deref()).map_err(|e| e.to_string())?;
    Ok(serde_json::to_value(account).unwrap())
}

/// 删除本地平台账号
#[tauri::command]
pub fn db_delete_account(id: String, state: State<DbState>) -> Result<String, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    repo.delete_platform_account(&id).map_err(|e| e.to_string())?;
    Ok("删除成功".to_string())
}

/// 获取本地发布任务列表
#[tauri::command]
pub fn db_list_publications(content_id: String, state: State<DbState>) -> Result<serde_json::Value, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    let publications = repo.list_publications(&content_id).map_err(|e| e.to_string())?;
    Ok(serde_json::to_value(publications).unwrap())
}

/// 创建本地发布任务
#[tauri::command]
pub fn db_create_publication(user_id: String, data: DbCreatePublication, state: State<DbState>) -> Result<serde_json::Value, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    let publication = repo.create_publication(&user_id, &data).map_err(|e| e.to_string())?;
    Ok(serde_json::to_value(publication).unwrap())
}

/// 更新发布任务状态
#[tauri::command]
pub fn db_update_publication_status(id: String, status: String, error_message: Option<String>, state: State<DbState>) -> Result<String, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    repo.update_publication_status(&id, &status, error_message.as_deref()).map_err(|e| e.to_string())?;
    Ok("更新成功".to_string())
}

/// 同步用户信息到本地数据库
#[tauri::command]
pub fn sync_user_to_local(user_id: String, email: Option<String>, username: Option<String>, nickname: Option<String>, avatar: Option<String>, state: State<DbState>) -> Result<String, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    repo.sync_user(&user_id, email.as_deref(), username.as_deref(), nickname.as_deref(), avatar.as_deref()).map_err(|e| e.to_string())?;
    Ok("用户同步成功".to_string())
}

/// 同步项目信息到本地数据库
#[tauri::command]
pub fn sync_project_to_local(project_id: String, user_id: String, name: String, description: Option<String>, state: State<DbState>) -> Result<String, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    repo.sync_project(&project_id, &user_id, &name, description.as_deref(), None).map_err(|e| e.to_string())?;
    Ok("项目同步成功".to_string())
}

/// 启动平台登录 - 打开浏览器让用户登录
#[tauri::command]
pub fn start_platform_login(platform: String, state: State<SidecarState>) -> Result<serde_json::Value, String> {
    let mut manager = state.lock().map_err(|e| e.to_string())?;
    let result = manager.call("start_platform_login", serde_json::json!({
        "platform": platform
    })).map_err(|e| e.to_string())?;
    Ok(result)
}

/// 检查平台登录状态
#[tauri::command]
pub fn check_platform_login_status(platform: String, account_id: String, state: State<SidecarState>) -> Result<serde_json::Value, String> {
    let mut manager = state.lock().map_err(|e| e.to_string())?;
    let result = manager.call("check_login_status", serde_json::json!({
        "platform": platform,
        "account_id": account_id
    })).map_err(|e| e.to_string())?;
    Ok(result)
}

/// 关闭登录浏览器
#[tauri::command]
pub fn close_login_browser(platform: String, account_id: String, state: State<SidecarState>) -> Result<serde_json::Value, String> {
    let mut manager = state.lock().map_err(|e| e.to_string())?;
    let result = manager.call("close_login_browser", serde_json::json!({
        "platform": platform,
        "account_id": account_id
    })).map_err(|e| e.to_string())?;
    Ok(result)
}

/// 同步单个账号的用户资料
#[tauri::command]
pub fn sync_account(platform: String, account_id: String, state: State<SidecarState>) -> Result<serde_json::Value, String> {
    let mut manager = state.lock().map_err(|e| e.to_string())?;
    let result = manager.call("sync_account", serde_json::json!({
        "platform": platform,
        "account_id": account_id
    })).map_err(|e| e.to_string())?;
    Ok(result)
}

/// 同步所有账号
#[tauri::command]
pub fn sync_all_accounts(state: State<SidecarState>) -> Result<serde_json::Value, String> {
    let mut manager = state.lock().map_err(|e| e.to_string())?;
    let result = manager.call("sync_all_accounts", serde_json::json!({})).map_err(|e| e.to_string())?;
    Ok(result)
}

/// 更新平台账号资料到本地数据库
#[tauri::command]
pub fn db_update_account_profile(
    id: String,
    account_name: Option<String>,
    avatar_url: Option<String>,
    followers_count: i64,
    following_count: i64,
    state: State<DbState>,
) -> Result<String, String> {
    let db = state.lock().map_err(|e| e.to_string())?;
    let repo = db.as_ref().ok_or("数据库未初始化")?;
    repo.update_platform_account_profile(&id, account_name.as_deref(), avatar_url.as_deref(), followers_count, following_count)
        .map_err(|e| e.to_string())?;
    Ok("更新成功".to_string())
}

// ============ 同步服务命令 ============

/// 开始全量同步
#[tauri::command]
pub async fn start_sync(app: AppHandle, user_id: String, token: String, state: State<'_, SyncState>) -> Result<String, String> {
    let engine = {
        let guard = state.lock().map_err(|e| e.to_string())?;
        guard.as_ref().ok_or("SyncEngine not initialized")?.clone()
    };

    // 异步执行，不阻塞命令返回
    // 注意：这里我们使用 tauri::async_runtime::spawn 来执行后台任务
    // 实际生产中可能需要更好的任务管理
    tauri::async_runtime::spawn(async move {
        match engine.start_sync(user_id, token).await {
            Ok(_) => {
                let _ = app.emit("sync-complete", ());
            }
            Err(e) => {
                eprintln!("[Sync] Background sync failed: {}", e);
                // 发送错误事件给前端
                let _ = app.emit("sync-error", e);
            }
        }
    });

    Ok("Sync started".to_string())
}

/// 获取同步状态
#[tauri::command]
pub fn get_sync_status(state: State<'_, SyncState>) -> Result<serde_json::Value, String> {
    let engine = {
        let guard = state.lock().map_err(|e| e.to_string())?;
        guard.as_ref().ok_or("SyncEngine not initialized")?.clone()
    };
    
    let status = engine.get_status();
    Ok(serde_json::to_value(status).unwrap())
}
