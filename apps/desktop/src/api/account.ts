/**
 * 平台账号 API
 * @author Ysf
 */
import request from "./request";

export interface CloudPlatformAccount {
  id?: string;
  project_id: string;
  platform: string;
  account_id: string;
  account_name?: string;
  avatar_url?: string;
  followers_count?: number;
  following_count?: number;
  posts_count?: number;
  is_active?: boolean;
  session_valid?: boolean;
  /**
   * 云端使用的扩展元数据字段（例如 likes_count, favorites_count 等）
   */
  metadata_info?: Record<string, unknown>;
}

// 获取项目下的平台账号列表
export function getAccountsApi(projectId: string) {
  return request.get<any, CloudPlatformAccount[]>(
    `/projects/${projectId}/accounts`,
  );
}

// 创建平台账号
export function createAccountApi(
  projectId: string,
  data: Omit<CloudPlatformAccount, "id" | "project_id">,
) {
  return request.post<any, CloudPlatformAccount>(
    `/projects/${projectId}/accounts`,
    data,
  );
}

// 更新平台账号
export function updateAccountApi(
  projectId: string,
  accountId: string,
  data: Partial<CloudPlatformAccount>,
) {
  return request.put<any, CloudPlatformAccount>(
    `/projects/${projectId}/accounts/${accountId}`,
    data,
  );
}

// 删除平台账号
export function deleteAccountApi(projectId: string, accountId: string) {
  return request.delete(`/projects/${projectId}/accounts/${accountId}`);
}

// 同步账号资料到云端
export function syncAccountToCloudApi(
  projectId: string,
  data: CloudPlatformAccount,
) {
  return request.post<any, CloudPlatformAccount>(
    `/projects/${projectId}/accounts/sync`,
    data,
  );
}
