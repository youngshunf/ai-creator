/**
 * 错误边界组件
 * @author Ysf
 */
import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });
    // 可以在这里上报错误到监控服务
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
          <div className="max-w-md w-full text-center space-y-6">
            <div className="w-16 h-16 mx-auto rounded-full bg-red-100 flex items-center justify-center">
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>

            <div className="space-y-2">
              <h1 className="text-2xl font-bold text-foreground">出错了</h1>
              <p className="text-muted-foreground">
                应用遇到了一个意外错误，请尝试刷新页面或返回首页。
              </p>
            </div>

            {this.state.error && (
              <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-left">
                <p className="text-sm font-medium text-red-800 mb-1">错误信息</p>
                <p className="text-sm text-red-600 font-mono break-all">
                  {this.state.error.message}
                </p>
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={this.handleReload}
                className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                刷新页面
              </button>
              <button
                onClick={this.handleGoHome}
                className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border hover:bg-accent transition-colors"
              >
                <Home className="w-4 h-4" />
                返回首页
              </button>
            </div>

            <button
              onClick={() => {
                const details = document.getElementById('error-details');
                if (details) {
                  details.classList.toggle('hidden');
                }
              }}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors inline-flex items-center gap-1"
            >
              <Bug className="w-3 h-3" />
              查看详细信息
            </button>

            <div id="error-details" className="hidden text-left">
              <pre className="p-4 rounded-xl bg-muted text-xs overflow-auto max-h-48">
                {this.state.errorInfo?.componentStack}
              </pre>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
