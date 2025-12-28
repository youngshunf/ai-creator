/**
 * 自动保存 Hook
 * @author Ysf
 */
import { useEffect, useRef, useCallback } from 'react';
import { useDraftStore } from '@/stores/useDraftStore';

interface UseAutoSaveOptions {
  draftId: string | null;
  content: string;
  title?: string;
  delay?: number;
  enabled?: boolean;
  onSave?: () => void;
  onError?: (error: Error) => void;
}

interface UseAutoSaveReturn {
  isSaving: boolean;
  lastSavedAt: number | null;
  saveNow: () => void;
}

export function useAutoSave({
  draftId,
  content,
  title,
  delay = 2000,
  enabled = true,
  onSave,
  onError,
}: UseAutoSaveOptions): UseAutoSaveReturn {
  const { updateDraft, setSaving, setLastSavedAt, isSaving, lastSavedAt } =
    useDraftStore();

  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastContentRef = useRef<string>(content);
  const lastTitleRef = useRef<string | undefined>(title);

  const save = useCallback(async () => {
    if (!draftId || !enabled) return;

    const hasContentChanged = content !== lastContentRef.current;
    const hasTitleChanged = title !== lastTitleRef.current;

    if (!hasContentChanged && !hasTitleChanged) return;

    setSaving(true);

    try {
      const updates: Record<string, unknown> = {
        isAutoSaved: true,
      };

      if (hasContentChanged) {
        updates.content = content;
        lastContentRef.current = content;
      }

      if (hasTitleChanged) {
        updates.title = title;
        lastTitleRef.current = title;
      }

      updateDraft(draftId, updates);
      setLastSavedAt(Date.now());
      onSave?.();
    } catch (error) {
      onError?.(error instanceof Error ? error : new Error('保存失败'));
    } finally {
      setSaving(false);
    }
  }, [
    draftId,
    content,
    title,
    enabled,
    updateDraft,
    setSaving,
    setLastSavedAt,
    onSave,
    onError,
  ]);

  const saveNow = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    save();
  }, [save]);

  useEffect(() => {
    if (!enabled || !draftId) return;

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      save();
    }, delay);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [content, title, delay, enabled, draftId, save]);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (content !== lastContentRef.current || title !== lastTitleRef.current) {
        e.preventDefault();
        saveNow();
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [content, title, saveNow]);

  return {
    isSaving,
    lastSavedAt,
    saveNow,
  };
}

export function formatLastSaved(timestamp: number | null): string {
  if (!timestamp) return '';

  const now = Date.now();
  const diff = now - timestamp;

  if (diff < 5000) {
    return '刚刚保存';
  } else if (diff < 60000) {
    return `${Math.floor(diff / 1000)} 秒前保存`;
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)} 分钟前保存`;
  } else {
    const date = new Date(timestamp);
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')} 保存`;
  }
}

export default useAutoSave;
