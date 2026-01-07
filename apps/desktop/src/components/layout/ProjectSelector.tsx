/**
 * 项目选择器组件
 * @author Ysf
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { Check, ChevronDown, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useProjectStore, Project } from '@/stores/useProjectStore';

interface ProjectSelectorProps {
    className?: string;
}

export function ProjectSelector({ className }: ProjectSelectorProps) {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const navigate = useNavigate();
    const { projects, currentProject, fetchProjects, setCurrentProject, isLoading } = useProjectStore();

    // 初始化时获取项目列表
    useEffect(() => {
        fetchProjects();
    }, [fetchProjects]);

    // 点击外部关闭下拉菜单
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleProjectSelect = (project: Project) => {
        setCurrentProject(project);
        setIsOpen(false);
    };

    return (
        <div className={cn('relative', className)} ref={dropdownRef}>
            {/* Trigger Button */}
            <button
                className="flex items-center space-x-2 px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-white/5 text-slate-700 dark:text-slate-200 transition-colors border border-transparent dark:border-white/5 hover:border-slate-200 dark:hover:border-white/10"
                onClick={() => setIsOpen(!isOpen)}
                disabled={isLoading}
            >
                <div
                    className={cn(
                        'w-2 h-2 rounded-full',
                        currentProject?.is_default ? 'bg-emerald-500' : 'bg-blue-500'
                    )}
                />
                <span className="font-medium text-sm max-w-[120px] truncate">
                    {isLoading ? '加载中...' : currentProject?.name || '选择项目'}
                </span>
                <ChevronDown
                    className={cn('w-4 h-4 text-slate-400 transition-transform', isOpen && 'rotate-180')}
                />
            </button>

            {/* Dropdown Menu */}
            {isOpen && (
                <div className="absolute right-0 top-full mt-2 w-72 bg-white dark:bg-slate-800 rounded-xl shadow-soft-lg ring-1 ring-slate-900/5 dark:ring-white/10 p-1 z-50 animate-in fade-in zoom-in-95 duration-100">
                    {/* Header */}
                    <div className="px-2 py-2 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                        切换项目
                    </div>

                    {/* Project List */}
                    <div className="max-h-48 overflow-y-auto">
                        {projects.length === 0 ? (
                            <div className="px-3 py-4 text-sm text-slate-500 text-center">
                                暂无项目，请创建新项目
                            </div>
                        ) : (
                            projects.map((project) => (
                                <button
                                    key={project.id}
                                    className={cn(
                                        'w-full flex items-center px-3 py-2 rounded-lg text-sm transition-colors',
                                        project.id === currentProject?.id
                                            ? 'bg-slate-50 dark:bg-white/5 text-slate-900 dark:text-white'
                                            : 'hover:bg-slate-50 dark:hover:bg-white/5 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                                    )}
                                    onClick={() => handleProjectSelect(project)}
                                >
                                    {project.id === currentProject?.id ? (
                                        <Check className="w-4 h-4 mr-2 text-primary-500 flex-shrink-0" />
                                    ) : (
                                        <div className="w-4 h-4 mr-2 flex-shrink-0" />
                                    )}
                                    <span className="truncate flex-1 text-left">{project.name}</span>
                                    {project.is_default && (
                                        <span className="ml-2 text-xs text-slate-400 dark:text-slate-500">默认</span>
                                    )}
                                </button>
                            ))
                        )}
                    </div>

                    {/* Divider */}
                    <div className="h-px bg-slate-100 dark:bg-slate-700/50 my-1" />

                    {/* Create Project Form */}
                    <button
                        onClick={() => {
                            setIsOpen(false);
                            navigate({ to: '/project/create' });
                        }}
                        className="w-full flex items-center px-3 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-white/5 text-primary-600 dark:text-primary-400 text-sm transition-colors font-medium"
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        创建新项目
                    </button>
                </div>
            )}
        </div>
    );
}
