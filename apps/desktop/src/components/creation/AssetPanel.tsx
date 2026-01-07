import { useState } from 'react';
import { Search, Image as ImageIcon, FileText, Plus, X } from 'lucide-react';
import { cn } from '@/lib/utils';

// Mock Data
const MOCK_IMAGES = [
    'https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=400&q=80',
    'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=400&q=80',
    'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&q=80',
    'https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400&q=80',
    'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400&q=80',
    'https://images.unsplash.com/photo-1516762689617-e1cffcef479d?w=400&q=80',
    'https://images.unsplash.com/photo-1627483262268-9c96d8e360c7?w=400&q=80',
    'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&q=80',
];

const MOCK_TEMPLATES = [
    {
        title: '金句：夏日清凉',
        content: '> 夏天的风我永远记得，清清楚楚地说要热死我。',
    },
    {
        title: '段落：穿搭法则',
        content: '要想夏天穿得清爽，颜色的选择至关重要。建议以低饱和度的色系为主，如白色、米色、浅蓝色等，视觉上就能降温 5 度。',
    },
    {
        title: '结尾：引导关注',
        content: '---\n\n如果你喜欢这篇笔记，别忘了点赞收藏哦！关注我，带你解锁更多时尚穿搭技巧 ✨',
    },
    {
        title: '标题模板：种草',
        content: '🔥 吹爆这个！[产品名]真的是我年度最爱，没有之一！',
    },
];

interface AssetPanelProps {
    onInsert: (type: 'image' | 'text', content: string) => void;
    className?: string;
}

export function AssetPanel({ onInsert, className }: AssetPanelProps) {
    const [activeTab, setActiveTab] = useState<'images' | 'templates'>('images');
    const [searchQuery, setSearchQuery] = useState('');

    const filteredImages = MOCK_IMAGES; // In real app, would filter
    const filteredTemplates = MOCK_TEMPLATES.filter(
        (t) => t.title.includes(searchQuery) || t.content.includes(searchQuery)
    );

    return (
        <div className={cn('flex flex-col h-full bg-white dark:bg-slate-900', className)}>
            {/* Search Bar */}
            <div className="p-4 pb-2">
                <div className="relative">
                    <input
                        type="text"
                        placeholder={activeTab === 'images' ? "搜索图片..." : "搜索模板..."}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full bg-slate-100 dark:bg-slate-800 rounded-lg pl-9 pr-8 py-2 text-sm focus:ring-1 focus:ring-primary-500 outline-none transition-colors text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500"
                    />
                    <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
                    {searchQuery && (
                        <button
                            onClick={() => setSearchQuery('')}
                            className="absolute right-2 top-2 p-0.5 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-400 transition-colors"
                        >
                            <X className="w-3 h-3" />
                        </button>
                    )}
                </div>
            </div>

            {/* Tabs */}
            <div className="px-4">
                <div className="flex border-b border-slate-100 dark:border-slate-800">
                    <button
                        onClick={() => setActiveTab('images')}
                        className={cn(
                            'flex-1 pb-2 text-sm font-medium transition-colors relative',
                            activeTab === 'images'
                                ? 'text-primary-600 dark:text-primary-400'
                                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
                        )}
                    >
                        <div className="flex items-center justify-center gap-1.5">
                            <ImageIcon className="w-4 h-4" />
                            <span>图片</span>
                        </div>
                        {activeTab === 'images' && (
                            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600 dark:bg-primary-400 rounded-t-full" />
                        )}
                    </button>
                    <button
                        onClick={() => setActiveTab('templates')}
                        className={cn(
                            'flex-1 pb-2 text-sm font-medium transition-colors relative',
                            activeTab === 'templates'
                                ? 'text-primary-600 dark:text-primary-400'
                                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
                        )}
                    >
                        <div className="flex items-center justify-center gap-1.5">
                            <FileText className="w-4 h-4" />
                            <span>模板</span>
                        </div>
                        {activeTab === 'templates' && (
                            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600 dark:bg-primary-400 rounded-t-full" />
                        )}
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                {activeTab === 'images' ? (
                    <div className="grid grid-cols-2 gap-2">
                        {filteredImages.map((src, index) => (
                            <div
                                key={index}
                                className="group relative aspect-square rounded-lg overflow-hidden bg-slate-100 dark:bg-slate-800 cursor-pointer"
                                onClick={() => onInsert('image', src)}
                            >
                                <img
                                    src={src}
                                    alt={`Mock ${index}`}
                                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                                />
                                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                                    <div className="w-8 h-8 rounded-full bg-white/90 backdrop-blur flex items-center justify-center shadow-sm transform scale-50 group-hover:scale-100 transition-transform">
                                        <Plus className="w-5 h-5 text-slate-900" />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="space-y-3">
                        {filteredTemplates.map((template, index) => (
                            <div
                                key={index}
                                className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 hover:border-primary-200 dark:hover:border-primary-500/30 cursor-pointer transition-colors group"
                                onClick={() => onInsert('text', template.content)}
                            >
                                <div className="flex items-center justify-between mb-1.5">
                                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                                        {template.title}
                                    </span>
                                    <Plus className="w-3.5 h-3.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                                </div>
                                <p className="text-xs text-slate-700 dark:text-slate-300 line-clamp-3">
                                    {template.content}
                                </p>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
