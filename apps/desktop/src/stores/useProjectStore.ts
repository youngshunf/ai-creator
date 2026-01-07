/**
 * 项目状态管理
 * @author Ysf
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
    getProjectsApi,
    createProjectApi,
    updateProjectApi,
    deleteProjectApi,
    setDefaultProjectApi
} from '@/api/project';

export interface Project {
    id: number;
    uuid: string;
    name: string;
    description?: string;
    industry?: string;
    sub_industries: string[];
    brand_name?: string;
    brand_tone?: string;
    brand_keywords: string[];
    topics: string[];
    keywords: string[];
    account_tags: string[];
    preferred_platforms: string[];
    content_style?: string;
    is_default: boolean;
    created_time: string;
    updated_time?: string;
}

export interface ProjectCreate {
    name: string;
    description?: string;
    industry?: string;
    sub_industries?: string[];
    brand_name?: string;
    brand_tone?: string;
    brand_keywords?: string[];
    topics?: string[];
    keywords?: string[];
    account_tags?: string[];
    preferred_platforms?: string[];
    content_style?: string;
}

export interface ProjectUpdate {
    name?: string;
    description?: string;
    industry?: string;
    sub_industries?: string[];
    brand_name?: string;
    brand_tone?: string;
    brand_keywords?: string[];
    topics?: string[];
    keywords?: string[];
    account_tags?: string[];
    preferred_platforms?: string[];
    content_style?: string;
}

interface ProjectState {
    // 状态
    projects: Project[];
    currentProject: Project | null;
    isLoading: boolean;
    error: string | null;

    // Actions
    fetchProjects: () => Promise<void>;
    createProject: (data: ProjectCreate) => Promise<Project>;
    updateProject: (id: number, data: ProjectUpdate) => Promise<void>;
    deleteProject: (id: number) => Promise<void>;
    setCurrentProject: (project: Project | null) => void;
    setCurrentProjectById: (id: number) => void;
    setDefaultProject: (id: number) => Promise<void>;
    clearError: () => void;
}

export const useProjectStore = create<ProjectState>()(
    persist(
        (set, get) => ({
            projects: [],
            currentProject: null,
            isLoading: false,
            error: null,

            fetchProjects: async () => {
                set({ isLoading: true, error: null });
                try {
                    const result = await getProjectsApi();
                    const projects = result.items || [];
                    set({ projects, isLoading: false });

                    // 如果没有当前项目，设置默认项目
                    const { currentProject, setCurrentProject } = get();
                    if (!currentProject && projects.length > 0) {
                        const defaultProject = projects.find((p) => p.is_default) || projects[0];
                        setCurrentProject(defaultProject);
                    }
                } catch (error) {
                    set({ error: String(error), isLoading: false });
                }
            },

            createProject: async (data: ProjectCreate) => {
                set({ isLoading: true, error: null });
                try {
                    const newProject = await createProjectApi(data);
                    set((state) => ({
                        projects: [...state.projects, newProject],
                        isLoading: false,
                        // 如果是第一个项目，自动设为当前项目
                        currentProject: state.projects.length === 0 ? newProject : state.currentProject,
                    }));
                    return newProject;
                } catch (error) {
                    set({ error: String(error), isLoading: false });
                    throw error;
                }
            },

            updateProject: async (id: number, data: ProjectUpdate) => {
                set({ isLoading: true, error: null });
                try {
                    await updateProjectApi(id, data);
                    set((state) => ({
                        projects: state.projects.map((p) => (p.id === id ? { ...p, ...data } : p)),
                        currentProject: state.currentProject?.id === id ? { ...state.currentProject, ...data } : state.currentProject,
                        isLoading: false,
                    }));
                } catch (error) {
                    set({ error: String(error), isLoading: false });
                    throw error;
                }
            },

            deleteProject: async (id: number) => {
                set({ isLoading: true, error: null });
                try {
                    await deleteProjectApi(id);
                    set((state) => {
                        const newProjects = state.projects.filter((p) => p.id !== id);
                        // 如果删除的是当前项目，切换到默认项目
                        let newCurrent = state.currentProject;
                        if (state.currentProject?.id === id) {
                            newCurrent = newProjects.find((p) => p.is_default) || newProjects[0] || null;
                        }
                        return { projects: newProjects, currentProject: newCurrent, isLoading: false };
                    });
                } catch (error) {
                    set({ error: String(error), isLoading: false });
                    throw error;
                }
            },

            setCurrentProject: async (project: Project | null) => {
                set({ currentProject: project });
                // 同步项目到本地数据库
                if (project) {
                    try {
                        const { invoke } = await import('@tauri-apps/api/core');
                        const { useAuthStore } = await import('./useAuthStore');
                        const userId = useAuthStore.getState().user?.id;
                        if (userId) {
                            await invoke('sync_project_to_local', {
                                projectId: project.uuid,
                                userId,
                                name: project.name,
                                description: project.description || null,
                            });
                            console.log('[Project] Synced to local database:', project.name);
                        }
                    } catch (err) {
                        console.warn('[Project] Failed to sync to local:', err);
                    }
                }
            },

            setCurrentProjectById: async (id: number) => {
                const { projects } = get();
                const project = projects.find((p) => p.id === id);
                if (project) {
                    set({ currentProject: project });
                    // 同步项目到本地数据库
                    try {
                        const { invoke } = await import('@tauri-apps/api/core');
                        const { useAuthStore } = await import('./useAuthStore');
                        const userId = useAuthStore.getState().user?.id;
                        if (userId) {
                            await invoke('sync_project_to_local', {
                                projectId: project.uuid,
                                userId,
                                name: project.name,
                                description: project.description || null,
                            });
                            console.log('[Project] Synced to local database:', project.name);
                        }
                    } catch (err) {
                        console.warn('[Project] Failed to sync to local:', err);
                    }
                }
            },

            setDefaultProject: async (id: number) => {
                set({ isLoading: true, error: null });
                try {
                    await setDefaultProjectApi(id);
                    set((state) => ({
                        projects: state.projects.map((p) => ({
                            ...p,
                            is_default: p.id === id,
                        })),
                        isLoading: false,
                    }));
                } catch (error) {
                    set({ error: String(error), isLoading: false });
                    throw error;
                }
            },

            clearError: () => set({ error: null }),
        }),
        {
            name: 'project-storage',
            partialize: (state) => ({
                currentProject: state.currentProject,
            }),
        }
    )
);
