/**
 * 发布预览面板
 * @author Ysf
 */
import { cn } from '@/lib/utils';

interface PreviewPanelProps {
  content: {
    title?: string;
    content: string;
    images: string[];
  };
  platform: string;
}

export function PreviewPanel({ content, platform }: PreviewPanelProps) {
  // 根据平台渲染不同的预览样式
  const renderPreview = () => {
    switch (platform) {
      case 'xiaohongshu':
        return <XiaohongshuPreview content={content} />;
      case 'wechat_mp':
        return <WeChatPreview content={content} />;
      case 'weibo':
        return <WeiboPreview content={content} />;
      default:
        return <DefaultPreview content={content} />;
    }
  };

  return (
    <div className="border rounded-lg overflow-hidden bg-background">
      {renderPreview()}
    </div>
  );
}

// 小红书预览
function XiaohongshuPreview({
  content,
}: {
  content: { title?: string; content: string; images: string[] };
}) {
  return (
    <div className="max-w-[375px] mx-auto">
      {/* 图片区域 */}
      <div className="aspect-[3/4] bg-muted flex items-center justify-center">
        {content.images.length > 0 ? (
          <img
            src={content.images[0]}
            alt="封面"
            className="w-full h-full object-cover"
          />
        ) : (
          <span className="text-muted-foreground">封面图片</span>
        )}
      </div>

      {/* 内容区域 */}
      <div className="p-4">
        {content.title && (
          <h3 className="font-bold text-lg mb-2 line-clamp-2">{content.title}</h3>
        )}
        <p className="text-sm text-muted-foreground line-clamp-4 whitespace-pre-wrap">
          {content.content}
        </p>
      </div>
    </div>
  );
}

// 微信公众号预览
function WeChatPreview({
  content,
}: {
  content: { title?: string; content: string; images: string[] };
}) {
  return (
    <div className="max-w-[375px] mx-auto p-4">
      {/* 标题 */}
      <h2 className="text-xl font-bold mb-4 text-center">
        {content.title || '无标题'}
      </h2>

      {/* 正文 */}
      <div className="prose prose-sm max-w-none">
        <p className="whitespace-pre-wrap">{content.content}</p>
      </div>
    </div>
  );
}

// 微博预览
function WeiboPreview({
  content,
}: {
  content: { title?: string; content: string; images: string[] };
}) {
  return (
    <div className="max-w-[375px] mx-auto p-4">
      {/* 用户信息 */}
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-muted" />
        <div>
          <p className="font-medium">用户名</p>
          <p className="text-xs text-muted-foreground">刚刚</p>
        </div>
      </div>

      {/* 内容 */}
      <p className="text-sm whitespace-pre-wrap mb-3">
        {content.title && `【${content.title}】`}
        {content.content}
      </p>

      {/* 图片网格 */}
      {content.images.length > 0 && (
        <div className="grid grid-cols-3 gap-1">
          {content.images.slice(0, 9).map((img, i) => (
            <div key={i} className="aspect-square bg-muted rounded" />
          ))}
        </div>
      )}
    </div>
  );
}

// 默认预览
function DefaultPreview({
  content,
}: {
  content: { title?: string; content: string; images: string[] };
}) {
  return (
    <div className="p-4">
      {content.title && <h3 className="font-bold mb-2">{content.title}</h3>}
      <p className="text-sm whitespace-pre-wrap">{content.content}</p>
    </div>
  );
}

export default PreviewPanel;
