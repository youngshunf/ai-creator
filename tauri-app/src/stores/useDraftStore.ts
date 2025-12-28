/**
 * 草稿状态管理
 * @author Ysf
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Draft {
  id: string;
  title: string;
  content: string;
  styleId?: string;
  platform?: string;
  tags: string[];
  createdAt: number;
  updatedAt: number;
  isAutoSaved: boolean;
}

interface DraftState {
  drafts: Draft[];
  currentDraftId: string | null;
  isSaving: boolean;
  lastSavedAt: number | null;

  // Actions
  createDraft: (draft: Omit<Draft, 'id' | 'createdAt' | 'updatedAt'>) => string;
  updateDraft: (id: string, updates: Partial<Draft>) => void;
  deleteDraft: (id: string) => void;
  setCurrentDraft: (id: string | null) => void;
  getCurrentDraft: () => Draft | null;
  setSaving: (isSaving: boolean) => void;
  setLastSavedAt: (timestamp: number) => void;
  clearAllDrafts: () => void;
}

export const useDraftStore = create<DraftState>()(
  persist(
    (set, get) => ({
      drafts: [],
      currentDraftId: null,
      isSaving: false,
      lastSavedAt: null,

      createDraft: (draftData) => {
        const id = `draft_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
        const now = Date.now();

        const newDraft: Draft = {
          ...draftData,
          id,
          createdAt: now,
          updatedAt: now,
        };

        set((state) => ({
          drafts: [newDraft, ...state.drafts],
          currentDraftId: id,
        }));

        return id;
      },

      updateDraft: (id, updates) => {
        set((state) => ({
          drafts: state.drafts.map((draft) =>
            draft.id === id
              ? { ...draft, ...updates, updatedAt: Date.now() }
              : draft
          ),
        }));
      },

      deleteDraft: (id) => {
        set((state) => ({
          drafts: state.drafts.filter((draft) => draft.id !== id),
          currentDraftId:
            state.currentDraftId === id ? null : state.currentDraftId,
        }));
      },

      setCurrentDraft: (id) => {
        set({ currentDraftId: id });
      },

      getCurrentDraft: () => {
        const state = get();
        if (!state.currentDraftId) return null;
        return state.drafts.find((d) => d.id === state.currentDraftId) || null;
      },

      setSaving: (isSaving) => {
        set({ isSaving });
      },

      setLastSavedAt: (timestamp) => {
        set({ lastSavedAt: timestamp });
      },

      clearAllDrafts: () => {
        set({ drafts: [], currentDraftId: null });
      },
    }),
    {
      name: 'ai-creator-drafts',
      partialize: (state) => ({
        drafts: state.drafts,
        currentDraftId: state.currentDraftId,
      }),
    }
  )
);

export default useDraftStore;
