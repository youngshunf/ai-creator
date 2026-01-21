/**
 * 统一请求封装
 * @author Ysf
 */
import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/useAuthStore';
import { invoke } from '@tauri-apps/api/core';

// 扩展 AxiosRequestConfig 类型
declare module 'axios' {
    interface AxiosRequestConfig {
        _retry?: boolean;
        __retryCount?: number;
    }
}

// 创建 Axios 实例
const request: AxiosInstance = axios.create({
    baseURL: import.meta.env.VITE_APP_API_URL || 'http://localhost:8010/api/v1',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// 请求拦截器
request.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const authStore = useAuthStore.getState();
        const token = authStore.getToken();

        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        return config;
    },
    (error: AxiosError) => {
        return Promise.reject(error);
    }
);

/**
 * 从错误响应中提取可读的错误消息
 */
function extractErrorMessage(error: AxiosError): string {
    // 优先使用后端返回的 msg 字段
    const responseData = error.response?.data as { code?: number; msg?: string; message?: string } | undefined;
    
    if (responseData?.msg) {
        return responseData.msg;
    }
    
    if (responseData?.message) {
        return responseData.message;
    }
    
    // 根据 HTTP 状态码提供友好的错误消息
    const status = error.response?.status;
    if (status) {
        const statusMessages: Record<number, string> = {
            400: '请求参数错误',
            401: '登录已过期，请重新登录',
            403: '没有权限访问',
            404: '请求的资源不存在',
            408: '请求超时',
            500: '服务器内部错误',
            502: '网关错误',
            503: '服务暂不可用',
            504: '网关超时',
        };
        return statusMessages[status] || `请求失败 (${status})`;
    }
    
    // 网络错误
    if (error.code === 'ECONNABORTED') {
        return '请求超时，请检查网络连接';
    }
    
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
        return '网络连接失败，请检查网络';
    }
    
    return '请求失败，请稍后重试';
}

/**
 * 创建带有友好消息的错误对象
 */
function createApiError(error: AxiosError): Error {
    const message = extractErrorMessage(error);
    const apiError = new Error(message);
    // 保留原始错误信息供调试
    (apiError as any).originalError = error;
    (apiError as any).status = error.response?.status;
    return apiError;
}

// 响应拦截器
request.interceptors.response.use(
    (response: AxiosResponse) => {
        // 假设后端返回格式为 { code: number, msg: string, data: any }
        const { code, msg, data } = response.data;

        // 如果没有 code 字段，可能是直接返回的数据或第三方接口
        if (code === undefined) {
            return response.data;
        }

        // 假设 200 为成功
        if (code === 200) {
            return data;
        }

        // 其他业务错误，使用后端返回的 msg
        return Promise.reject(new Error(msg || '请求失败'));
    },
    async (error: AxiosError) => {
        const originalRequest = error.config;

        if (!originalRequest) {
            return Promise.reject(createApiError(error));
        }

        // 处理 401 未授权 (Token 过期)
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            const authStore = useAuthStore.getState();
            const refreshToken = authStore.getRefreshToken();

            if (refreshToken) {
                try {
                    // 尝试刷新 Token
                    // 注意：这里不能用同一个 instance，否则会死循环
                    const refreshResponse = await axios.post(
                        `${import.meta.env.VITE_APP_API_URL || 'http://localhost:8010/api/v1'}/auth/refresh`,
                        {},
                        {
                            headers: {
                                Cookie: `refresh_token=${refreshToken}`
                            }
                        }
                    );

                    if (refreshResponse.status === 200 && refreshResponse.data.code === 200) {
                        const { access_token, access_token_expire_time } = refreshResponse.data.data;
                        const expiresAt = new Date(access_token_expire_time).getTime();

                        // 更新 Store
                        authStore.setToken(access_token, expiresAt);

                        // 更新当前请求的 Header 并重试
                        originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
                        return request(originalRequest);
                    }
                } catch (refreshError) {
                    console.error('RefreshToken 失败:', refreshError);
                }
            }

            // 刷新失败，登出并跳转
            authStore.logout();
            window.location.reload(); // 重载页面以触发路由跳转到登录页
            return Promise.reject(createApiError(error));
        }

        // 其他错误：提取友好的错误消息
        return Promise.reject(createApiError(error));
    }
);

export default request;
