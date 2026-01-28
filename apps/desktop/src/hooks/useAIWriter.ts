/**
 * AI 写作 Hook
 * @author Ysf
 */
import { useState, useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";
import { WritingStyle, getStyleById } from "@/config/writingStyles";
import { useAuthStore } from "@/stores/useAuthStore";

export interface AIWriterOptions {
  topic: string;
  styleId: string;
  platform?: string;
  keywords?: string[];
  additionalPrompt?: string;
}

export interface AIWriterResult {
  title: string;
  content: string;
  tags: string[];
}

export interface UseAIWriterReturn {
  isGenerating: boolean;
  progress: number;
  error: string | null;
  result: AIWriterResult | null;
  generate: (options: AIWriterOptions) => Promise<AIWriterResult | null>;
  cancel: () => void;
  reset: () => void;
}

export function useAIWriter(): UseAIWriterReturn {
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AIWriterResult | null>(null);
  const [abortController, setAbortController] =
    useState<AbortController | null>(null);

  const generate = useCallback(
    async (options: AIWriterOptions): Promise<AIWriterResult | null> => {
      const {
        topic,
        styleId,
        platform,
        keywords = [],
        additionalPrompt,
      } = options;

      if (!topic.trim()) {
        setError("请输入创作主题");
        return null;
      }

      const style = getStyleById(styleId);
      if (!style) {
        setError("请选择写作风格");
        return null;
      }

      setIsGenerating(true);
      setProgress(0);
      setError(null);
      setResult(null);

      const controller = new AbortController();
      setAbortController(controller);

      try {
        setProgress(10);

        const prompt = buildPrompt(
          topic,
          style,
          platform,
          keywords,
          additionalPrompt,
        );

        setProgress(20);

        // 使用当前登录用户的 UUID 作为 user_id，未登录时退化为本地默认用户
        const authState = useAuthStore.getState();
        const effectiveUserId = authState.user?.uuid ?? "current-user";

        const response = await invoke<{
          success: boolean;
          data?: AIWriterResult;
          error?: string;
        }>("execute_ai_writing", {
          request: {
            graph_name: "content-creation",
            inputs: {
              topic,
              platform: platform || style.platform[0],
              style: styleId,
              keywords,
              system_prompt: style.systemPrompt,
              user_prompt: prompt,
            },
            user_id: effectiveUserId,
            access_token: authState.getToken() || "",
          },
        });

        setProgress(90);

        if (!response.success || !response.data) {
          throw new Error(response.error || "生成失败");
        }

        setProgress(100);
        setResult(response.data);
        return response.data;
      } catch (err) {
        if (controller.signal.aborted) {
          setError("已取消生成");
        } else {
          const errorMessage =
            err instanceof Error ? err.message : "生成失败，请重试";
          setError(errorMessage);
        }
        return null;
      } finally {
        setIsGenerating(false);
        setAbortController(null);
      }
    },
    [],
  );

  const cancel = useCallback(() => {
    if (abortController) {
      abortController.abort();
    }
  }, [abortController]);

  const reset = useCallback(() => {
    setIsGenerating(false);
    setProgress(0);
    setError(null);
    setResult(null);
  }, []);

  return {
    isGenerating,
    progress,
    error,
    result,
    generate,
    cancel,
    reset,
  };
}

function buildPrompt(
  topic: string,
  style: WritingStyle,
  platform?: string,
  keywords: string[] = [],
  additionalPrompt?: string,
): string {
  let prompt = `请为主题「${topic}」创作一篇${style.name}风格的内容。\n\n`;

  if (platform) {
    prompt += `目标平台：${platform}\n`;
  }

  if (keywords.length > 0) {
    prompt += `关键词：${keywords.join("、")}\n`;
  }

  if (additionalPrompt) {
    prompt += `\n额外要求：${additionalPrompt}\n`;
  }

  prompt += `\n请按照以下格式输出（使用 Markdown 格式）：

## 标题
[吸引眼球，符合平台特点的标题]

## 正文
[使用 Markdown 格式编写正文内容，包括：
- 使用 ## 和 ### 作为小标题
- 使用 **粗体** 强调重点
- 使用 - 或 1. 创建列表
- 适当使用 > 引用
- 符合${style.name}风格]

## 标签
[3-5个推荐标签，用逗号分隔]`;

  return prompt;
}

export default useAIWriter;
