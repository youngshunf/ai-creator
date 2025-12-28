/**
 * 首页路由 - 精致版
 * @author Ysf
 */
import { createFileRoute } from '@tanstack/react-router';
import { PenTool, Send, BarChart3, Sparkles } from 'lucide-react';

export const Route = createFileRoute('/')({
  component: HomePage,
});

function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-8 animate-fade-in">
      <div className="text-center space-y-3">
        <h1 className="text-4xl font-semibold gradient-text tracking-tight">创流</h1>
        <p className="text-lg text-slate-500">自媒体创作者的 AI 超级大脑</p>
      </div>
      <div className="grid grid-cols-2 gap-4 mt-6 max-w-xl w-full">
        <FeatureCard
          icon={PenTool}
          title="AI 创作"
          description="智能写作、风格模板"
          color="blue"
        />
        <FeatureCard
          icon={Send}
          title="多平台发布"
          description="一键发布多平台"
          color="purple"
        />
        <FeatureCard
          icon={BarChart3}
          title="数据分析"
          description="统一数据看板"
          color="green"
        />
        <FeatureCard
          icon={Sparkles}
          title="热点追踪"
          description="AI 选题推荐"
          color="orange"
        />
      </div>
    </div>
  );
}

interface FeatureCardProps {
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  title: string;
  description: string;
  color: 'blue' | 'purple' | 'green' | 'orange';
}

const colorStyles = {
  blue: 'text-brand-blue bg-brand-blue/10',
  purple: 'text-brand-purple bg-brand-purple/10',
  green: 'text-success bg-success/10',
  orange: 'text-orange bg-orange/10',
};

function FeatureCard({ icon: Icon, title, description, color }: FeatureCardProps) {
  return (
    <div className="p-5 rounded-2xl bg-white shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 cursor-pointer group">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 ${colorStyles[color]}`}>
        <Icon className="w-5 h-5" strokeWidth={1.75} />
      </div>
      <h3 className="font-semibold text-sm text-slate-900 mb-1">{title}</h3>
      <p className="text-xs text-slate-500">{description}</p>
    </div>
  );
}
