/**
 * 平台账号 API
 * @author Ysf
 */
import request from './request';

export interface CloudPlatformAccount {
  id?: number;
  uuid?: string;
  project_id: number;
  platform: string;
  account_id: string;
  account_name?: string;
  avatar_url?: string;
  followers_count?: number;
  following_count?: number;
  posts_count?: number;
  is_active?: boolean;
  session_valid?: boolean;
  metadata?: Record<string, unknown>;
}

// 获取项目下的平台账号列表
export function getAccountsApi(projectId: number) {
  return request.get<any, CloudPlatformAccount[]>(`/projects/${projectId}/accounts`);
}

// 创建平台账号
export function createAccountApi(projectId: number, data: Omit<CloudPlatformAccount, 'id' | 'uuid' | 'project_id'>) {
  return request.post<any, CloudPlatformAccount>(`/projects/${projectId}/accounts`, data);
}

// 更新平台账号
export function updateAccountApi(projectId: number, accountId: number, data: Partial<CloudPlatformAccount>) {
  return request.put<any, CloudPlatformAccount>(`/projects/${projectId}/accounts/${accountId}`, data);
}

// 删除平台账号
export function deleteAccountApi(projectId: number, accountId: number) {
  return request.delete(`/projects/${projectId}/accounts/${accountId}`);
}

// 同步账号资料到云端
export function syncAccountToCloudApi(projectId: number, data: CloudPlatformAccount) {
  return request.post<any, CloudPlatformAccount>(`/projects/${projectId}/accounts/sync`, data);
}
