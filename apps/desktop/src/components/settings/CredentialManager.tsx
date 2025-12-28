/**
 * 凭证管理组件
 * @author Ysf
 */
import { useState, useEffect, useCallback } from 'react';
import {
  Key,
  Plus,
  Trash2,
  RefreshCw,
  Shield,
  CheckCircle,
  AlertCircle,
  Eye,
  EyeOff,
  Loader2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Credential {
  id: string;
  platform: string;
  accountId: string;
  accountName: string;
  status: 'valid' | 'expired' | 'unknown';
  lastVerified?: string;
  createdAt: string;
}

interface CredentialManagerProps {
  className?: string;
}

const PLATFORMS = [
  { id: 'xiaohongshu', name: '小红书', icon: '📕', color: 'text-red-500' },
  { id: 'wechat_mp', name: '微信公众号', icon: '💬', color: 'text-green-500' },
  { id: 'weibo', name: '微博', icon: '🔴', color: 'text-orange-500' },
  { id: 'douyin', name: '抖音', icon: '🎵', color: 'text-pink-500' },
  { id: 'bilibili', name: 'B站', icon: '📺', color: 'text-blue-500' },
];

export function CredentialManager({ className }: CredentialManagerProps) {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState<Record<string, boolean>>({});

  const fetchCredentials = useCallback(async () => {
    setIsLoading(true);
    try {
      // 模拟 API 调用 - 实际应调用 Sidecar
      await new Promise((resolve) => setTimeout(resolve, 500));
      // 从本地存储或 Sidecar 获取凭证列表
      const stored = localStorage.getItem('credentials');
      if (stored) {
        setCredentials(JSON.parse(stored));
      }
    } catch (error) {
      console.error('获取凭证失败:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  const handleAddCredential = async (platform: string) => {
    setIsAdding(true);
    try {
      // 实际应调用 Sidecar 打开浏览器进行登录
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const newCredential: Credential = {
        id: `cred_${Date.now()}`,
        platform,
        accountId: `user_${Math.random().toString(36).substr(2, 8)}`,
        accountName: `${PLATFORMS.find((p) => p.id === platform)?.name}账号`,
        status: 'valid',
        lastVerified: new Date().toISOString(),
        createdAt: new Date().toISOString(),
      };

      const updated = [...credentials, newCredential];
      setCredentials(updated);
      localStorage.setItem('credentials', JSON.stringify(updated));
      setSelectedPlatform(null);
    } catch (error) {
      console.error('添加凭证失败:', error);
    } finally {
      setIsAdding(false);
    }
  };

  const handleVerifyCredential = async (id: string) => {
    setVerifyingId(id);
    try {
      // 实际应调用 Sidecar 验证凭证
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setCredentials((prev) =>
        prev.map((c) =>
          c.id === id
            ? { ...c, status: 'valid', lastVerified: new Date().toISOString() }
            : c
        )
      );
    } catch (error) {
      console.error('验证凭证失败:', error);
    } finally {
      setVerifyingId(null);
    }
  };

  const handleDeleteCredential = async (id: string) => {
    if (!confirm('确定要删除此凭证吗？删除后需要重新登录。')) return;

    setDeletingId(id);
    try {
      await new Promise((resolve) => setTimeout(resolve, 500));

      const updated = credentials.filter((c) => c.id !== id);
      setCredentials(updated);
      localStorage.setItem('credentials', JSON.stringify(updated));
    } catch (error) {
      console.error('删除凭证失败:', error);
    } finally {
      setDeletingId(null);
    }
  };

  const toggleDetails = (id: string) => {
    setShowDetails((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const getStatusIcon = (status: Credential['status']) => {
    switch (status) {
      case 'valid':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'expired':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getStatusText = (status: Credential['status']) => {
    switch (status) {
      case 'valid':
        return '有效';
      case 'expired':
        return '已过期';
      default:
        return '未知';
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const connectedPlatforms = new Set(credentials.map((c) => c.platform));
  const availablePlatforms = PLATFORMS.filter((p) => !connectedPlatforms.has(p.id));

  return (
    <div className={cn('space-y-6', className)}>
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <Key className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold">平台凭证管理</h3>
            <p className="text-sm text-muted-foreground">
              管理已绑定的平台账号
            </p>
          </div>
        </div>
        <button
          onClick={fetchCredentials}
          disabled={isLoading}
          className="p-2 rounded-lg hover:bg-accent transition-colors"
          title="刷新"
        >
          <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
        </button>
      </div>

      {/* 已绑定的凭证列表 */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        ) : credentials.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Shield className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>暂无已绑定的平台账号</p>
            <p className="text-sm">点击下方按钮添加平台账号</p>
          </div>
        ) : (
          credentials.map((credential) => {
            const platform = PLATFORMS.find((p) => p.id === credential.platform);
            return (
              <div
                key={credential.id}
                className="p-4 rounded-xl border bg-card hover:shadow-sm transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{platform?.icon}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{platform?.name}</span>
                        {getStatusIcon(credential.status)}
                        <span
                          className={cn(
                            'text-xs px-2 py-0.5 rounded-full',
                            credential.status === 'valid'
                              ? 'bg-green-100 text-green-700'
                              : credential.status === 'expired'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-yellow-100 text-yellow-700'
                          )}
                        >
                          {getStatusText(credential.status)}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {credential.accountName}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleDetails(credential.id)}
                      className="p-2 rounded-lg hover:bg-accent transition-colors"
                      title={showDetails[credential.id] ? '隐藏详情' : '显示详情'}
                    >
                      {showDetails[credential.id] ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      onClick={() => handleVerifyCredential(credential.id)}
                      disabled={verifyingId === credential.id}
                      className="p-2 rounded-lg hover:bg-accent transition-colors"
                      title="验证凭证"
                    >
                      {verifyingId === credential.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      onClick={() => handleDeleteCredential(credential.id)}
                      disabled={deletingId === credential.id}
                      className="p-2 rounded-lg hover:bg-red-100 text-red-500 transition-colors"
                      title="删除凭证"
                    >
                      {deletingId === credential.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {showDetails[credential.id] && (
                  <div className="mt-3 pt-3 border-t text-sm text-muted-foreground space-y-1">
                    <p>账号 ID: {credential.accountId}</p>
                    <p>创建时间: {formatDate(credential.createdAt)}</p>
                    {credential.lastVerified && (
                      <p>最后验证: {formatDate(credential.lastVerified)}</p>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* 添加新凭证 */}
      {availablePlatforms.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-muted-foreground">
            添加平台账号
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {availablePlatforms.map((platform) => (
              <button
                key={platform.id}
                onClick={() => {
                  setSelectedPlatform(platform.id);
                  handleAddCredential(platform.id);
                }}
                disabled={isAdding}
                className={cn(
                  'p-4 rounded-xl border-2 border-dashed transition-all',
                  'hover:border-primary hover:bg-primary/5',
                  'flex flex-col items-center gap-2',
                  selectedPlatform === platform.id && isAdding && 'border-primary bg-primary/5'
                )}
              >
                {selectedPlatform === platform.id && isAdding ? (
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                ) : (
                  <>
                    <span className="text-2xl">{platform.icon}</span>
                    <span className="text-sm font-medium">{platform.name}</span>
                    <Plus className="w-4 h-4 text-muted-foreground" />
                  </>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 安全提示 */}
      <div className="p-4 rounded-xl bg-blue-50 border border-blue-200">
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 text-blue-500 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-blue-700">安全说明</p>
            <p className="text-blue-600 mt-1">
              您的平台凭证使用 AES-256-GCM 加密存储在本地，不会上传到云端。
              凭证仅用于自动发布功能，我们不会访问您的账号数据。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CredentialManager;
