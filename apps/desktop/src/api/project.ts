/**
 * 项目管理 API
 * @author Ysf
 */
import request from './request';
import type { Project, ProjectCreate, ProjectUpdate } from '@/stores/useProjectStore';

interface ProjectListResult {
    items: Project[];
    total: number;
}

export function getProjectsApi() {
    return request.get<any, ProjectListResult>('/projects');
}

export function createProjectApi(data: ProjectCreate) {
    return request.post<any, Project>('/projects', data);
}

export function updateProjectApi(id: number, data: ProjectUpdate) {
    return request.put<any, Project>(`/projects/${id}`, data);
}

export function deleteProjectApi(id: number) {
    return request.delete(`/projects/${id}`);
}

export function setDefaultProjectApi(id: number) {
    return request.put(`/projects/${id}/default`);
}
