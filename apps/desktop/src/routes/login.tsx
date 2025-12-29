/**
 * 登录页面
 * @author Ysf
 */
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { useState, useEffect } from 'react';
import { useAuth, useAuthStore } from '@/hooks/useAuth';

export const Route = createFileRoute('/login')({
  component: LoginPage,
});

type LoginTab = 'phone' | 'password';

function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { sendCode, phoneLogin, passwordLogin, isLoading, error, clearError } = useAuth();

  const [tab, setTab] = useState<LoginTab>('phone');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [countdown, setCountdown] = useState(0);

  // 已登录则跳转首页
  useEffect(() => {
    if (isAuthenticated) {
      navigate({ to: '/' });
    }
  }, [isAuthenticated, navigate]);

  // 倒计时
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleSendCode = async () => {
    if (!phone || countdown > 0) return;
    const success = await sendCode(phone);
    if (success) setCountdown(60);
  };

  const handlePhoneLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const success = await phoneLogin(phone, code);
    if (success) navigate({ to: '/' });
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const success = await passwordLogin(username, password);
    if (success) navigate({ to: '/' });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-full max-w-md p-8 bg-white rounded-2xl shadow-xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">创流</h1>
          <p className="text-gray-500 mt-2">自媒体创作者的 AI 超级大脑</p>
        </div>

        {/* Tab 切换 */}
        <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
          <button
            className={`flex-1 py-2 rounded-md text-sm font-medium transition ${
              tab === 'phone' ? 'bg-white text-blue-600 shadow' : 'text-gray-600'
            }`}
            onClick={() => { setTab('phone'); clearError(); }}
          >
            手机号登录
          </button>
          <button
            className={`flex-1 py-2 rounded-md text-sm font-medium transition ${
              tab === 'password' ? 'bg-white text-blue-600 shadow' : 'text-gray-600'
            }`}
            onClick={() => { setTab('password'); clearError(); }}
          >
            密码登录
          </button>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-lg">
            {error}
          </div>
        )}

        {/* 手机号登录表单 */}
        {tab === 'phone' && (
          <form onSubmit={handlePhoneLogin} className="space-y-4">
            <div>
              <input
                type="tel"
                placeholder="请输入手机号"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                maxLength={11}
              />
            </div>
            <div className="flex gap-3">
              <input
                type="text"
                placeholder="验证码"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="flex-1 px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                maxLength={6}
              />
              <button
                type="button"
                onClick={handleSendCode}
                disabled={!phone || countdown > 0 || isLoading}
                className="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
              >
                {countdown > 0 ? `${countdown}s` : '获取验证码'}
              </button>
            </div>
            <button
              type="submit"
              disabled={!phone || !code || isLoading}
              className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '登录中...' : '登录 / 注册'}
            </button>
            <p className="text-xs text-gray-400 text-center">
              未注册的手机号将自动创建账号
            </p>
          </form>
        )}

        {/* 密码登录表单 */}
        {tab === 'password' && (
          <form onSubmit={handlePasswordLogin} className="space-y-4">
            <div>
              <input
                type="text"
                placeholder="用户名 / 手机号"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={!username || !password || isLoading}
              className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '登录中...' : '登录'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
