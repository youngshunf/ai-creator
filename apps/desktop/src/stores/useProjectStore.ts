/**
 * 项目状态管理
 * @author Ysf
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { invoke } from "@tauri-apps/api/core";
import { useAuthStore } from "./useAuthStore";

// 对应 Rust 后端 Project 结构 (JSON 字符串字段)
// 注意：id 实际上传递的是项目 UID（projects.uid），user_id 为用户 UID（sys_user.uuid）
interface RawProject {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  industry?: string;
  sub_industries?: string; // JSON string
  brand_name?: string;
  brand_tone?: string;
  brand_keywords?: string; // JSON string
  topics?: string; // JSON string
  keywords?: string; // JSON string
  account_tags?: string; // JSON string
  preferred_platforms?: string; // JSON string
  content_style?: string;
  is_default: boolean;
  created_at: number;
  updated_at: number;
}

// 前端使用的 Project 结构 (解析后的数组)
export interface Project {
  id: string;
  user_id: string;
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
  created_at: number;
  updated_at: number;
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
  fetchProjects: (retryCount?: number) => Promise<void>;
  createProject: (data: ProjectCreate) => Promise<Project>;
  updateProject: (id: string, data: ProjectUpdate) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  setCurrentProject: (project: Project | null) => void;
  setCurrentProjectById: (id: string) => void;
  setDefaultProject: (id: string) => Promise<void>;
  clearError: () => void;
  syncProjectToCloud: (project: Project) => Promise<void>;
}

// 辅助函数：解析 JSON 字符串为数组
const parseJsonArray = (jsonStr?: string | null): string[] => {
  if (!jsonStr) return [];
  try {
    const parsed = JSON.parse(jsonStr);
    return Array.isArray(parsed) ? parsed : [];
  } catch (e) {
    console.warn("Failed to parse JSON:", jsonStr);
    return [];
  }
};

// 辅助函数：将 RawProject 转换为 Project
const mapRawToProject = (raw: RawProject): Project => ({
  ...raw,
  sub_industries: parseJsonArray(raw.sub_industries),
  brand_keywords: parseJsonArray(raw.brand_keywords),
  topics: parseJsonArray(raw.topics),
  keywords: parseJsonArray(raw.keywords),
  account_tags: parseJsonArray(raw.account_tags),
  preferred_platforms: parseJsonArray(raw.preferred_platforms),
});

export const useProjectStore = create<ProjectState>()(
  persist(
    (set, get) => ({
      projects: [],
      currentProject: null,
      isLoading: false,
      error: null,

      fetchProjects: async (retryCount = 0) => {
        set({ isLoading: true, error: null });
        try {
          // 获取当前用户ID
          const userStore = useAuthStore.getState();
          // 如果用户未登录，使用默认ID (为了离线支持)
          const effectiveUserId = userStore.user?.uuid
            ? String(userStore.user.uuid)
            : "current-user";

          console.log(
            "[ProjectStore] Fetching projects for user:",
            effectiveUserId,
          );
          const rawProjects = await invoke<RawProject[]>("db_list_projects", {
            userId: effectiveUserId,
          });

          // 转换并更新状态
          const projects = rawProjects.map(mapRawToProject);
          const defaultProject = projects.find((p) => p.is_default);
          set({
            projects,
            currentProject: defaultProject || projects[0] || null,
            isLoading: false,
          });
        } catch (error) {
          const errorMsg = String(error);
          // 如果是数据库未初始化错误，重试（最多 10 次，每次 1 秒）
          // 注意：Rust 返回的错误信息可能是 "数据库未初始化"
          if (
            (errorMsg.includes("数据库未初始化") ||
              errorMsg.includes("Database not initialized")) &&
            retryCount < 10
          ) {
            console.warn(
              `[ProjectStore] Database not ready, retrying... (${retryCount + 1}/10)`,
            );
            await new Promise((resolve) => setTimeout(resolve, 1000)); // 等待 1000ms
            return get().fetchProjects(retryCount + 1);
          }

          console.error("[ProjectStore] Failed to fetch projects:", errorMsg);
          set({ error: errorMsg, isLoading: false });
        }
      },

      createProject: async (data: ProjectCreate) => {
        set({ isLoading: true, error: null });
        try {
          const user = useAuthStore.getState().user;
          const effectiveUserId = user?.uuid
            ? String(user.uuid)
            : "current-user";

          const rawProject = await invoke<RawProject>("db_create_project", {
            userId: effectiveUserId,
            data,
          });

          const newProject = mapRawToProject(rawProject);

          set((state) => ({
            projects: [newProject, ...state.projects], // 新项目排在前面
            isLoading: false,
            // 如果是第一个项目，自动设为当前项目
            currentProject:
              state.projects.length === 0 ? newProject : state.currentProject,
          }));

          // 触发后台同步
          get().syncProjectToCloud(newProject);

          return newProject;
        } catch (error) {
          set({ error: String(error), isLoading: false });
          throw error;
        }
      },

      updateProject: async (id: string, data: ProjectUpdate) => {
        set({ isLoading: true, error: null });
        try {
          // 调用后端更新命令 (需要后端支持 db_update_project)
          await invoke("db_update_project", { id, data });

          set((state) => {
            const updatedProjects = state.projects.map((p) =>
              p.id === id ? { ...p, ...data } : p,
            );
            const updatedCurrent =
              state.currentProject?.id === id
                ? { ...state.currentProject, ...data }
                : state.currentProject;

            return {
              projects: updatedProjects,
              currentProject: updatedCurrent,
              isLoading: false,
            };
          });

          // 触发后台同步
          const updatedProject = get().projects.find((p) => p.id === id);
          if (updatedProject) {
            get().syncProjectToCloud(updatedProject);
          }
        } catch (error) {
          set({ error: String(error), isLoading: false });
          throw error;
        }
      },

      deleteProject: async (id: string) => {
        set({ isLoading: true, error: null });
        try {
          await invoke("db_delete_project", { id });

          set((state) => {
            const newProjects = state.projects.filter((p) => p.id !== id);
            // 如果删除的是当前项目，切换到默认项目
            let newCurrent = state.currentProject;
            if (state.currentProject?.id === id) {
              newCurrent =
                newProjects.find((p) => p.is_default) || newProjects[0] || null;
            }
            return {
              projects: newProjects,
              currentProject: newCurrent,
              isLoading: false,
            };
          });

          // TODO: 触发云端删除
        } catch (error) {
          set({ error: String(error), isLoading: false });
          throw error;
        }
      },

      setCurrentProject: (project: Project | null) => {
        set({ currentProject: project });
      },

      setCurrentProjectById: (id: string) => {
        const { projects } = get();
        const project = projects.find((p) => p.id === id);
        if (project) {
          set({ currentProject: project });
        }
      },

      setDefaultProject: async (id: string) => {
        try {
          const auth = useAuthStore.getState();
          const effectiveUserId = auth.user?.uuid
            ? String(auth.user.uuid)
            : "current-user";

          // 调用本地命令，保证同一用户只有一个默认项目
          await invoke("db_set_default_project", {
            userId: effectiveUserId,
            projectId: id,
          });

          // 本地状态更新：仅一个默认项目
          set((state) => {
            const updatedProjects = state.projects.map((p) => ({
              ...p,
              is_default: p.id === id,
            }));
            const newCurrent =
              state.currentProject && state.currentProject.id === id
                ? { ...state.currentProject, is_default: true }
                : updatedProjects.find((p) => p.id === id) ||
                  state.currentProject;

            return {
              projects: updatedProjects,
              currentProject: newCurrent,
            };
          });

          // 尝试将默认项目状态同步到云端（失败不影响本地使用）
          const target = get().projects.find((p) => p.id === id);
          if (target) {
            get().syncProjectToCloud({ ...target, is_default: true });
          }
        } catch (error) {
          console.error("[ProjectStore] Failed to set default project:", error);
          set({ error: String(error) });
        }
      },

      clearError: () => set({ error: null }),

      syncProjectToCloud: async (project: Project) => {
        // 简单的同步占位符
        console.log("Syncing project to cloud:", project.name);
        // 这里可以调用原来的 API: createProjectApi / updateProjectApi
        // 但为了 MVP 离线优先，我们只记录日志或放到同步队列中
      },
    }),
    {
      name: "project-storage",
      partialize: (state) => ({
        currentProject: state.currentProject,
      }),
    },
  ),
);
