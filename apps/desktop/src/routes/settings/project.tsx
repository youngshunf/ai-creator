/**
 * 项目设置页面
 * @author Ysf
 */
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { ArrowLeft, Save, Trash2, Star, Plus, X } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  useProjectStore,
  ProjectCreate,
  ProjectUpdate,
} from "@/stores/useProjectStore";

export const Route = createFileRoute("/settings/project")({
  component: ProjectSettingsPage,
});

// 行业选项
const INDUSTRIES = [
  "科技",
  "美妆",
  "时尚",
  "美食",
  "旅游",
  "教育",
  "健身",
  "金融",
  "游戏",
  "影视",
  "音乐",
  "摄影",
  "生活方式",
  "母婴",
  "宠物",
  "其他",
];

function ProjectSettingsPage() {
  const navigate = useNavigate();
  const {
    projects,
    currentProject,
    fetchProjects,
    createProject,
    updateProject,
    deleteProject,
    setDefaultProject,
    setCurrentProject,
    isLoading,
  } = useProjectStore();

  // 编辑状态
  const [isCreating, setIsCreating] = useState(false);
  const [editingProject, setEditingProject] = useState<string | null>(null);
  const [formData, setFormData] = useState<ProjectCreate>({
    name: "",
    description: "",
    industry: "",
    sub_industries: [],
    brand_name: "",
    brand_tone: "",
    brand_keywords: [],
    topics: [],
    keywords: [],
  });

  // Tag input states
  const [topicInput, setTopicInput] = useState("");
  const [keywordInput, setKeywordInput] = useState("");
  const [brandKeywordInput, setBrandKeywordInput] = useState("");

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // 打开编辑模式
  const handleEdit = (project: typeof currentProject) => {
    if (!project) return;
    setEditingProject(project.id);
    setFormData({
      name: project.name,
      description: project.description || "",
      industry: project.industry || "",
      sub_industries: project.sub_industries || [],
      brand_name: project.brand_name || "",
      brand_tone: project.brand_tone || "",
      brand_keywords: project.brand_keywords || [],
      topics: project.topics || [],
      keywords: project.keywords || [],
    });
    setIsCreating(false);
  };

  // 保存项目
  const handleSave = async () => {
    try {
      if (isCreating) {
        const newProject = await createProject(formData);
        setCurrentProject(newProject);
        setIsCreating(false);
      } else if (editingProject) {
        await updateProject(editingProject, formData as ProjectUpdate);
        setEditingProject(null);
      }
      resetForm();
    } catch (error) {
      console.error("保存项目失败:", error);
    }
  };

  // 删除项目
  const handleDelete = async (id: string) => {
    if (confirm("确定要删除这个项目吗？此操作不可恢复。")) {
      try {
        await deleteProject(id);
        setEditingProject(null);
      } catch (error) {
        console.error("删除项目失败:", error);
      }
    }
  };

  // 设为默认
  const handleSetDefault = async (id: string) => {
    try {
      await setDefaultProject(id);
    } catch (error) {
      console.error("设置默认项目失败:", error);
    }
  };

  // 重置表单
  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      industry: "",
      sub_industries: [],
      brand_name: "",
      brand_tone: "",
      brand_keywords: [],
      topics: [],
      keywords: [],
    });
    setTopicInput("");
    setKeywordInput("");
    setBrandKeywordInput("");
  };

  // 取消编辑
  const handleCancel = () => {
    setIsCreating(false);
    setEditingProject(null);
    resetForm();
  };

  // 添加 tag
  const addTag = (
    type: "topics" | "keywords" | "brand_keywords",
    value: string,
  ) => {
    if (!value.trim()) return;
    setFormData((prev) => ({
      ...prev,
      [type]: [...(prev[type] || []), value.trim()],
    }));
  };

  // 移除 tag
  const removeTag = (
    type: "topics" | "keywords" | "brand_keywords",
    index: number,
  ) => {
    setFormData((prev) => ({
      ...prev,
      [type]: prev[type]?.filter((_, i) => i !== index) || [],
    }));
  };

  const isEditing = isCreating || editingProject !== null;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate({ to: "/settings" })}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold">项目管理</h1>
            <p className="text-sm text-slate-500">管理你的创作项目</p>
          </div>
        </div>
        {!isEditing && (
          <button
            onClick={() => navigate({ to: "/project/create" })}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            新建项目
          </button>
        )}
      </div>

      <div className="flex-1 flex gap-6 overflow-hidden">
        {/* 项目列表 */}
        <div
          className={cn(
            "w-80 overflow-y-auto space-y-2",
            isEditing && "hidden md:block",
          )}
        >
          {projects.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              暂无项目，点击右上角创建
            </div>
          ) : (
            projects.map((project) => (
              <button
                key={project.id}
                onClick={() => handleEdit(project)}
                className={cn(
                  "w-full p-4 rounded-xl border text-left transition-all",
                  editingProject === project.id
                    ? "border-primary-500 bg-primary-50 dark:bg-primary-500/10"
                    : "border-slate-200 dark:border-slate-700 hover:border-primary-300 hover:bg-slate-50 dark:hover:bg-slate-800",
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate">
                        {project.name}
                      </span>
                      {project.is_default && (
                        <Star className="w-4 h-4 text-amber-500 fill-amber-500 flex-shrink-0" />
                      )}
                    </div>
                    {project.description && (
                      <p className="text-sm text-slate-500 truncate mt-1">
                        {project.description}
                      </p>
                    )}
                    {project.industry && (
                      <span className="inline-block mt-2 text-xs px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded">
                        {project.industry}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>

        {/* 编辑表单 */}
        {isEditing && (
          <div className="flex-1 overflow-y-auto">
            <div className="w-full space-y-6">
              {/* 基本信息 */}
              <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-700">
                <h3 className="font-semibold mb-4">基本信息</h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      项目名称 *
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          name: e.target.value,
                        }))
                      }
                      className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      placeholder="例如：美妆种草号"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      项目描述
                    </label>
                    <textarea
                      value={formData.description || ""}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          description: e.target.value,
                        }))
                      }
                      className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                      rows={3}
                      placeholder="简要描述这个项目的定位..."
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      行业领域
                    </label>
                    <select
                      value={formData.industry || ""}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          industry: e.target.value,
                        }))
                      }
                      className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    >
                      <option value="">选择行业</option>
                      {INDUSTRIES.map((ind) => (
                        <option key={ind} value={ind}>
                          {ind}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* 品牌信息 */}
              <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-700">
                <h3 className="font-semibold mb-4">品牌信息</h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      品牌名称
                    </label>
                    <input
                      type="text"
                      value={formData.brand_name || ""}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          brand_name: e.target.value,
                        }))
                      }
                      className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      placeholder="品牌或个人 IP 名称"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      品牌调性
                    </label>
                    <input
                      type="text"
                      value={formData.brand_tone || ""}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          brand_tone: e.target.value,
                        }))
                      }
                      className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      placeholder="例如：专业、亲和、有趣、高端"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      品牌关键词
                    </label>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {formData.brand_keywords?.map((kw, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-sm"
                        >
                          {kw}
                          <button
                            onClick={() => removeTag("brand_keywords", i)}
                            className="hover:text-red-500"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                    <input
                      type="text"
                      value={brandKeywordInput}
                      onChange={(e) => setBrandKeywordInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addTag("brand_keywords", brandKeywordInput);
                          setBrandKeywordInput("");
                        }
                      }}
                      className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      placeholder="输入后回车添加"
                    />
                  </div>
                </div>
              </div>

              {/* 关注话题 */}
              <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-700">
                <h3 className="font-semibold mb-4">关注话题</h3>
                <div className="flex flex-wrap gap-2 mb-2">
                  {formData.topics?.map((topic, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded text-sm"
                    >
                      {topic}
                      <button
                        onClick={() => removeTag("topics", i)}
                        className="hover:text-red-500"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <input
                  type="text"
                  value={topicInput}
                  onChange={(e) => setTopicInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addTag("topics", topicInput);
                      setTopicInput("");
                    }
                  }}
                  className="w-full px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="输入话题后回车添加，例如：护肤心得"
                />
              </div>

              {/* 操作按钮 */}
              <div className="flex items-center justify-between pt-4">
                <div>
                  {editingProject &&
                    !projects.find((p) => p.id === editingProject)
                      ?.is_default && (
                      <button
                        onClick={() => handleDelete(editingProject)}
                        className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                        disabled={isLoading}
                      >
                        <Trash2 className="w-4 h-4" />
                        删除项目
                      </button>
                    )}
                </div>
                <div className="flex items-center gap-3">
                  {editingProject &&
                    !projects.find((p) => p.id === editingProject)
                      ?.is_default && (
                      <button
                        onClick={() => handleSetDefault(editingProject)}
                        className="flex items-center gap-2 px-4 py-2 text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded-lg transition-colors"
                        disabled={isLoading}
                      >
                        <Star className="w-4 h-4" />
                        设为默认
                      </button>
                    )}
                  <button
                    onClick={handleCancel}
                    className="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                    disabled={isLoading}
                  >
                    取消
                  </button>
                  <button
                    onClick={handleSave}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg font-medium transition-colors"
                    disabled={isLoading || !formData.name.trim()}
                  >
                    <Save className="w-4 h-4" />
                    {isLoading ? "保存中..." : "保存"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 空状态提示 */}
        {!isEditing && projects.length > 0 && (
          <div className="flex-1 flex items-center justify-center text-slate-500">
            点击左侧项目进行编辑
          </div>
        )}
      </div>
    </div>
  );
}
