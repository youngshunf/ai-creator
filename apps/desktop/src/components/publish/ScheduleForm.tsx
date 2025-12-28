/**
 * 定时发布表单
 * @author Ysf
 */
import { useState } from 'react';
import { Calendar, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ScheduleFormProps {
  platforms: string[];
  onSchedule: (scheduledTime: string) => void;
}

export function ScheduleForm({ platforms, onSchedule }: ScheduleFormProps) {
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (date && time) {
      const scheduledTime = `${date}T${time}:00`;
      onSchedule(scheduledTime);
    }
  };

  // 获取最小日期（今天）
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="max-w-md mx-auto">
      <h3 className="text-lg font-semibold mb-6">设置定时发布</h3>

      {platforms.length === 0 ? (
        <div className="text-center text-muted-foreground py-8">
          <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>请先选择要发布的平台</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 日期选择 */}
          <div>
            <label className="block text-sm font-medium mb-2">
              <Calendar className="w-4 h-4 inline mr-2" />
              发布日期
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              min={today}
              className={cn(
                'w-full px-4 py-2 rounded-lg border bg-background',
                'focus:outline-none focus:ring-2 focus:ring-ring'
              )}
              required
            />
          </div>

          {/* 时间选择 */}
          <div>
            <label className="block text-sm font-medium mb-2">
              <Clock className="w-4 h-4 inline mr-2" />
              发布时间
            </label>
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className={cn(
                'w-full px-4 py-2 rounded-lg border bg-background',
                'focus:outline-none focus:ring-2 focus:ring-ring'
              )}
              required
            />
          </div>

          {/* 平台列表 */}
          <div>
            <label className="block text-sm font-medium mb-2">发布平台</label>
            <div className="flex flex-wrap gap-2">
              {platforms.map((p) => (
                <span
                  key={p}
                  className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm"
                >
                  {p === 'xiaohongshu' && '小红书'}
                  {p === 'wechat_mp' && '微信公众号'}
                  {p === 'weibo' && '微博'}
                </span>
              ))}
            </div>
          </div>

          {/* 提交按钮 */}
          <button
            type="submit"
            className={cn(
              'w-full py-3 rounded-lg font-medium transition-colors',
              'bg-primary text-primary-foreground',
              'hover:bg-primary/90',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            设置定时发布
          </button>
        </form>
      )}
    </div>
  );
}

export default ScheduleForm;
