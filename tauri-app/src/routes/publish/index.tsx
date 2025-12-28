/**
 * 发布中心页面
 * @author Ysf
 */
import { createFileRoute } from '@tanstack/react-router';
import { PublishCenter } from '@/components/publish/PublishCenter';

export const Route = createFileRoute('/publish/')({
  component: PublishPage,
});

function PublishPage() {
  return <PublishCenter />;
}
