/**
 * 认证 API
 * @author Ysf
 */
import request from "./request";
import type { User } from "@/stores/useAuthStore";

interface LoginParams {
  username?: string;
  password?: string;
  phone?: string;
  code?: string;
}

export interface LoginResult {
  access_token: string;
  access_token_expire_time: string;
  refresh_token: string;
  refresh_token_expire_time: string;
  user: User;
  llm_token: string;
}

export function loginApi(params: LoginParams) {
  // 根据是否有 password 决定是密码登录还是手机号登录
  if (params.password) {
    return request.post<any, LoginResult>("/auth/login", params);
  } else {
    return request.post<any, LoginResult>("/auth/phone-login", params);
  }
}

export function logoutApi() {
  return request.post("/auth/logout");
}

export function getUserInfoApi() {
  return request.get<any, User>("/sys/users/me");
}

export function sendVerificationCodeApi(phone: string) {
  return request.post("/auth/send-code", { phone });
}
