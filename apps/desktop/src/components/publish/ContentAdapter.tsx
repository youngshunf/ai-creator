/**
 * 内容适配器组件 - 显示各平台内容限制和适配状态
 * @author Ysf
 */
import { AlertCircle, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ContentAdapterProps {
  content: {
    title?: string;
    content: string;
    images: string[];
  };
  platforms: string[];
}

// 平台内容限制配置
const PLATFORM_LIMITS: Record<
  string,
  {
    name: string;
    titleMax: number;
    contentMax: number;
    imagesMax: number;
    titleRequired: boolean;
  }
> = {
  xiaohongshu: {
    name: '小红书',
    titleMax: 20,
    contentMax: 1000,
    imagesMax: 18,
    titleRequired: false,
  },
  wechat_mp: {
    name: '微信公众号',
    titleMax: 64,
    contentMax: 20000,
    imagesMax: 20,
    titleRequired: true,
  },
  weibo: {
    name: '微博',
    titleMax: 0,
    contentMax: 2000,
    imagesMax: 9,
    titleRequired: false,
  },
};

export function ContentAdapter({ content, platforms }: ContentAdapterProps) {
  const checkPlatform = (platformId: string) => {
    const limits = PLATFORM_LIMITS[platformId];
    if (!limits) return { valid: true, issues: [] };

    const issues: string[] = [];

    // 检查标题
    if (limits.titleRequired && !content.title) {
      issues.push('需要标题');
    }
    if (content.title && limits.titleMax > 0 && content.title.length > limits.titleMax) {
      issues.push(`标题超出 ${content.title.length - limits.titleMax} 字`);
    }

    // 检查正文
    if (content.content.length > limits.contentMax) {
      issues.push(`正文超出 ${content.content.length - limits.contentMax} 字`);
    }

    // 检查图片
    if (content.images.length > limits.imagesMax) {
      issues.push(`图片超出 ${content.images.length - limits.imagesMax} 张`);
    }

    return {
      valid: issues.length === 0,
      issues,
    };
  };

  return (
    <div className="space-y-3">
      <h4 className="font-medium">内容适配检查</h4>
      {platforms.map((platformId) => {
        const limits = PLATFORM_LIMITS[platformId];
        const check = checkPlatform(platformId);

        if (!limits) return null;

        return (
          <div
            key={platformId}
            className={cn(
              'p-3 rounded-lg border',
              check.valid ? 'border-green-200 bg-green-50' : 'border-amber-200 bg-amber-50'
            )}
          >
            <div className="flex items-center gap-2 mb-2">
              {check.valid ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : (
                <AlertCircle className="w-4 h-4 text-amber-600" />
              )}
              <span className="font-medium">{limits.name}</span>
            </div>

            {check.valid ? (
              <p className="text-sm text-green-700">内容符合平台要求</p>
            ) : (
              <ul className="text-sm text-amber-700 space-y-1">
                {check.issues.map((issue, i) => (
                  <li key={i}>• {issue}</li>
                ))}
              </ul>
            )}

            <div className="mt-2 text-xs text-muted-foreground">
              标题 {content.title?.length || 0}/{limits.titleMax || '无限制'} ·
              正文 {content.content.length}/{limits.contentMax} ·
              图片 {content.images.length}/{limits.imagesMax}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default ContentAdapter;
