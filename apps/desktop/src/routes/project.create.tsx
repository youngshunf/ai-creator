/**
 * 创建项目页面
 * @author Ysf
 */
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useState } from 'react';
import { useProjectStore, type ProjectCreate } from '@/stores/useProjectStore';
import { ChevronLeft, Plus, X } from 'lucide-react';

export const Route = createFileRoute('/project/create')({
    component: ProjectCreatePage,
});

function ProjectCreatePage() {
    const navigate = useNavigate();
    const { createProject, isLoading } = useProjectStore();

    // 表单状态
    const [formData, setFormData] = useState<ProjectCreate>({
        name: '',
        description: '',
        industry: '',
        sub_industries: [],
        brand_name: '',
        brand_tone: '',
        brand_keywords: [],
        topics: [],
        keywords: [],
        account_tags: [],
        preferred_platforms: [],
        content_style: '',
    });

    // 临时输入状态
    const [tempInputs, setTempInputs] = useState({
        sub_industry: '',
        brand_keyword: '',
        topic: '',
        keyword: '',
        account_tag: '',
        platform: '',
    });

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleArrayAdd = (field: keyof ProjectCreate, inputField: keyof typeof tempInputs) => {
        const value = tempInputs[inputField].trim();
        if (value && Array.isArray(formData[field]) && !formData[field]?.includes(value)) {
            setFormData(prev => ({
                ...prev,
                [field]: [...(prev[field] as string[] || []), value]
            }));
            setTempInputs(prev => ({ ...prev, [inputField]: '' }));
        }
    };

    const handleArrayRemove = (field: keyof ProjectCreate, itemToRemove: string) => {
        if (Array.isArray(formData[field])) {
            setFormData(prev => ({
                ...prev,
                [field]: (prev[field] as string[]).filter(item => item !== itemToRemove)
            }));
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await createProject(formData);
            navigate({ to: '/settings/project' });
        } catch (error) {
            console.error('Failed to create project:', error);
            // TODO: Show toast
        }
    };

    return (
        <div className="flex flex-col h-full bg-gray-50">
            {/* 顶部导航 */}
            <div className="flex items-center px-6 py-4 bg-white border-b border-gray-200">
                <button
                    onClick={() => navigate({ to: '/settings/project' })}
                    className="p-2 mr-4 hover:bg-gray-100 rounded-lg transition-colors"
                >
                    <ChevronLeft className="w-5 h-5 text-gray-600" />
                </button>
                <h1 className="text-xl font-bold text-gray-800">创建新项目</h1>
            </div>

            {/* 表单内容 */}
            <div className="flex-1 overflow-y-auto p-6">
                <form onSubmit={handleSubmit} className="max-w-4xl mx-auto space-y-8">

                    {/* 1. 基础信息 */}
                    <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            <span className="w-1 h-6 bg-blue-500 rounded-full mr-3"></span>
                            基础信息
                        </h2>
                        <div className="grid grid-cols-1 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">项目名称 *</label>
                                <input
                                    type="text"
                                    name="name"
                                    value={formData.name}
                                    onChange={handleInputChange}
                                    required
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="例如：科技资讯自媒体"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">项目描述</label>
                                <textarea
                                    name="description"
                                    value={formData.description}
                                    onChange={handleInputChange}
                                    rows={3}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="简单描述这个项目的目标和受众..."
                                />
                            </div>
                        </div>
                    </section>

                    {/* 2. 行业与品牌 */}
                    <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            <span className="w-1 h-6 bg-purple-500 rounded-full mr-3"></span>
                            行业与品牌
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">所属行业</label>
                                <input
                                    type="text"
                                    name="industry"
                                    value={formData.industry}
                                    onChange={handleInputChange}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="例如：科技数码"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">品牌名称</label>
                                <input
                                    type="text"
                                    name="brand_name"
                                    value={formData.brand_name}
                                    onChange={handleInputChange}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="例如：极客视界"
                                />
                            </div>

                            {/* 子行业 - 数组输入 */}
                            <div className="col-span-2">
                                <label className="block text-sm font-medium text-gray-700 mb-2">细分领域 / 子行业</label>
                                <div className="flex gap-2 mb-2">
                                    <input
                                        type="text"
                                        value={tempInputs.sub_industry}
                                        onChange={(e) => setTempInputs(prev => ({ ...prev, sub_industry: e.target.value }))}
                                        className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="输入后回车或点击添加"
                                        onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleArrayAdd('sub_industries', 'sub_industry'))}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => handleArrayAdd('sub_industries', 'sub_industry')}
                                        className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                                    >
                                        <Plus className="w-5 h-5" />
                                    </button>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {formData.sub_industries?.map((item, index) => (
                                        <span key={index} className="px-3 py-1 bg-purple-50 text-purple-600 rounded-full text-sm flex items-center">
                                            {item}
                                            <button
                                                type="button"
                                                onClick={() => handleArrayRemove('sub_industries', item)}
                                                className="ml-2 hover:text-purple-800"
                                            >
                                                <X className="w-3 h-3" />
                                            </button>
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">品牌调性</label>
                                <input
                                    type="text"
                                    name="brand_tone"
                                    value={formData.brand_tone}
                                    onChange={handleInputChange}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="例如：专业、幽默、亲切"
                                />
                            </div>
                        </div>
                    </section>

                    {/* 3. 内容策略 */}
                    <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            <span className="w-1 h-6 bg-green-500 rounded-full mr-3"></span>
                            内容策略
                        </h2>
                        <div className="grid grid-cols-1 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">内容风格</label>
                                <input
                                    type="text"
                                    name="content_style"
                                    value={formData.content_style}
                                    onChange={handleInputChange}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="例如：深度解析、快节奏解说"
                                />
                            </div>

                            {/* 关注话题 */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">核心话题</label>
                                <div className="flex gap-2 mb-2">
                                    <input
                                        type="text"
                                        value={tempInputs.topic}
                                        onChange={(e) => setTempInputs(prev => ({ ...prev, topic: e.target.value }))}
                                        className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="添加话题"
                                        onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleArrayAdd('topics', 'topic'))}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => handleArrayAdd('topics', 'topic')}
                                        className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                                    >
                                        <Plus className="w-5 h-5" />
                                    </button>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {formData.topics?.map((item, index) => (
                                        <span key={index} className="px-3 py-1 bg-green-50 text-green-600 rounded-full text-sm flex items-center">
                                            {item}
                                            <button type="button" onClick={() => handleArrayRemove('topics', item)} className="ml-2">
                                                <X className="w-3 h-3" />
                                            </button>
                                        </span>
                                    ))}
                                </div>
                            </div>

                            {/* 平台偏好 */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">偏好发布平台</label>
                                <div className="flex gap-2 mb-2">
                                    <input
                                        type="text"
                                        value={tempInputs.platform}
                                        onChange={(e) => setTempInputs(prev => ({ ...prev, platform: e.target.value }))}
                                        className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="例如：抖音、小红书"
                                        onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleArrayAdd('preferred_platforms', 'platform'))}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => handleArrayAdd('preferred_platforms', 'platform')}
                                        className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
                                    >
                                        <Plus className="w-5 h-5" />
                                    </button>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {formData.preferred_platforms?.map((item, index) => (
                                        <span key={index} className="px-3 py-1 bg-orange-50 text-orange-600 rounded-full text-sm flex items-center">
                                            {item}
                                            <button type="button" onClick={() => handleArrayRemove('preferred_platforms', item)} className="ml-2">
                                                <X className="w-3 h-3" />
                                            </button>
                                        </span>
                                    ))}
                                </div>
                            </div>

                        </div>
                    </section>

                    {/* 提交按钮 */}
                    <div className="pt-4 flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={() => navigate({ to: '/settings/project' })}
                            className="px-6 py-2.5 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors font-medium"
                        >
                            取消
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="px-8 py-2.5 bg-blue-600 text-white rounded-lg shadow-lg shadow-blue-200 hover:bg-blue-700 transition-all font-medium disabled:opacity-50"
                        >
                            {isLoading ? '创建中...' : '立即创建项目'}
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
}
