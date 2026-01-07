/**
 * 发布队列组件
 * @author Ysf
 */
import { CheckCircle, XCircle, Loader2, RefreshCw, ExternalLink } from 'lucide-react';
import { PublishTask, usePublishStore } from '@/stores/usePublishStore';

interface PublishQueueProps {
  tasks: PublishTask[];
}

const platformConfig: Record<string, { bg: string; text: string; name: string }> = {
  xiaohongshu: { bg: 'bg-red-500', text: '书', name: '小红书' },
  wechat: { bg: 'bg-green-500', text: '微', name: '微信公众号' },
  douyin: { bg: 'bg-black', text: '抖', name: '抖音' },
};

const statusConfig: Record<string, { icon: React.ReactNode; text: string; color: string }> = {
  pending: { icon: <div className="w-2 h-2 rounded-full bg-slate-400" />, text: '等待中', color: 'text-slate-500' },
  publishing: { icon: <Loader2 className="w-4 h-4 animate-spin text-primary-500" />, text: '发布中', color: 'text-primary-500' },
  success: { icon: <CheckCircle className="w-4 h-4 text-green-500" />, text: '已发布', color: 'text-green-500' },
  failed: { icon: <XCircle className="w-4 h-4 text-red-500" />, text: '失败', color: 'text-red-500' },
};

export function PublishQueue({ tasks }: PublishQueueProps) {
  const { retryTask } = usePublishStore();

  if (tasks.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500 dark:text-slate-400">
        暂无发布任务
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {tasks.map((task) => {
        const platform = platformConfig[task.platform] || { bg: 'bg-slate-500', text: '?', name: task.platform };
        const status = statusConfig[task.status] || statusConfig.pending;

        return (
          <div
            key={task.id}
            className="flex items-center justify-between p-4 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700"
          >
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-full ${platform.bg} flex items-center justify-center text-white text-xs font-bold`}>
                {platform.text}
              </div>
              <div>
                <div className="font-medium text-slate-900 dark:text-white">{platform.name}</div>
                <div className={`flex items-center gap-1.5 text-sm ${status.color}`}>
                  {status.icon}
                  <span>{status.text}</span>
                  {task.error_message && (
                    <span className="text-red-500 text-xs">- {task.error_message}</span>
                  )}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {task.status === 'failed' && (
                <button
                  onClick={() => retryTask(task.id)}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-500/10 rounded-lg transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  重试
                </button>
              )}
              {task.status === 'success' && task.platform_post_url && (
                <a
                  href={task.platform_post_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  查看
                </a>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
