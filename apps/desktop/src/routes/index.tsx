/**
 * 首页路由 - Tech Startup + SaaS 风格
 * @author Ysf
 * @updated 2026-01-07
 */
import { createFileRoute, Link } from '@tanstack/react-router';
import { Eye, TrendingUp, UserPlus, MessageCircle, TrendingDown, RefreshCw, Plus } from 'lucide-react';

export const Route = createFileRoute('/')({
  component: HomePage,
});

function HomePage() {
  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 hover:shadow-lg transition-shadow cursor-pointer">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-500 dark:text-slate-400 font-medium">昨日总阅读</span>
            <div className="p-2 rounded-lg bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400">
              <Eye className="w-5 h-5" />
            </div>
          </div>
          <div className="flex items-baseline space-x-2">
            <h3 className="text-3xl font-heading font-bold">42.5k</h3>
            <span className="badge badge-success flex items-center">
              <TrendingUp className="w-3 h-3 mr-1" />
              +12.5%
            </span>
          </div>
        </div>

        <div className="glass-card p-6 hover:shadow-lg transition-shadow cursor-pointer">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-500 dark:text-slate-400 font-medium">新增粉丝</span>
            <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400">
              <UserPlus className="w-5 h-5" />
            </div>
          </div>
          <div className="flex items-baseline space-x-2">
            <h3 className="text-3xl font-heading font-bold">856</h3>
            <span className="badge badge-success flex items-center">
              <TrendingUp className="w-3 h-3 mr-1" />
              +5.2%
            </span>
          </div>
        </div>

        <div className="glass-card p-6 hover:shadow-lg transition-shadow cursor-pointer">
          <div className="flex items-center justify-between mb-4">
            <span className="text-slate-500 dark:text-slate-400 font-medium">全平台互动</span>
            <div className="p-2 rounded-lg bg-pink-50 dark:bg-pink-500/10 text-pink-500 dark:text-pink-400">
              <MessageCircle className="w-5 h-5" />
            </div>
          </div>
          <div className="flex items-baseline space-x-2">
            <h3 className="text-3xl font-heading font-bold">3.2k</h3>
            <span className="badge badge-error flex items-center">
              <TrendingDown className="w-3 h-3 mr-1" />
              -2.1%
            </span>
          </div>
        </div>
      </div>

      {/* Recent Drafts */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-heading font-bold">近期草稿</h2>
          <Link to="/creation" className="text-sm text-primary-600 dark:text-primary-400 hover:underline cursor-pointer">
            查看全部
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Draft Card 1 */}
          <div className="group glass-card overflow-hidden hover:shadow-lg transition-all cursor-pointer">
            <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700 relative">
              <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-sm">
                <span className="btn-primary">继续编辑</span>
              </div>
            </div>
            <div className="p-4">
              <div className="flex items-center space-x-2 mb-2">
                <span className="badge badge-error text-[10px]">小红书</span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400">2小时前</span>
              </div>
              <h3 className="font-medium line-clamp-2 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                适合夏天的5种清爽穿搭，显瘦又高级！
              </h3>
            </div>
          </div>

          {/* Draft Card 2 */}
          <div className="group glass-card overflow-hidden hover:shadow-lg transition-all cursor-pointer">
            <div className="aspect-video bg-gradient-to-br from-indigo-100 to-slate-200 dark:from-indigo-900 dark:to-slate-800 relative">
              <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-sm">
                <span className="btn-primary">继续编辑</span>
              </div>
            </div>
            <div className="p-4">
              <div className="flex items-center space-x-2 mb-2">
                <span className="badge bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 text-[10px]">公众号</span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400">昨天</span>
              </div>
              <h3 className="font-medium line-clamp-2 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                深入解析 AI Agent 的未来发展趋势
              </h3>
            </div>
          </div>

          {/* New Creation Card */}
          <Link
            to="/creation"
            className="flex flex-col items-center justify-center glass-card border-2 border-dashed border-slate-200 dark:border-slate-700 hover:border-primary-500 dark:hover:border-primary-500 transition-all group h-full min-h-[240px] cursor-pointer"
          >
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3 group-hover:scale-110 group-hover:bg-primary-50 dark:group-hover:bg-primary-500/10 transition-all">
              <Plus className="w-6 h-6 text-slate-400 group-hover:text-primary-600 dark:group-hover:text-primary-400" />
            </div>
            <span className="font-medium text-slate-500 group-hover:text-primary-600 dark:group-hover:text-primary-400">
              新建创作
            </span>
          </Link>
        </div>
      </section>

      {/* Platform Status */}
      <section>
        <h2 className="text-lg font-heading font-bold mb-4">平台状态</h2>
        <div className="glass-card overflow-hidden divide-y divide-[rgb(var(--color-border))]">
          <div className="flex items-center justify-between p-4 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors cursor-pointer">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center font-bold text-white text-xs shadow-md">
                书
              </div>
              <div>
                <p className="font-medium">美妆种草号</p>
                <p className="text-xs text-slate-500 flex items-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-success mr-1.5"></span>
                  连接正常
                </p>
              </div>
            </div>
            <button className="btn-secondary flex items-center text-sm">
              <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
              同步数据
            </button>
          </div>

          <div className="flex items-center justify-between p-4 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors cursor-pointer">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 rounded-full bg-black flex items-center justify-center font-bold text-white text-xs shadow-md border border-slate-700">
                抖音
              </div>
              <div>
                <p className="font-medium">科技测评</p>
                <p className="text-xs text-error flex items-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-error mr-1.5"></span>
                  凭证已失效
                </p>
              </div>
            </div>
            <button className="btn-cta text-sm">
              重新登录
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
