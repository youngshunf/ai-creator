/**
 * TipTap 富文本编辑器组件
 * @author Ysf
 */
import { useEditor, EditorContent } from '@tiptap/react';
import { BubbleMenu } from '@tiptap/react/menus';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';
import Placeholder from '@tiptap/extension-placeholder';
import CharacterCount from '@tiptap/extension-character-count';
import Link from '@tiptap/extension-link';
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight';
import { common, createLowlight } from 'lowlight';
import { useCallback, useEffect } from 'react';
import { EditorToolbar } from './EditorToolbar';
import { AIAssistMenu } from './AIAssistMenu';
import { cn } from '@/lib/utils';

const lowlight = createLowlight(common);

export interface TipTapEditorProps {
  content?: string;
  onChange?: (content: string) => void;
  onSelectionChange?: (text: string) => void;
  placeholder?: string;
  maxLength?: number;
  className?: string;
  editable?: boolean;
  showToolbar?: boolean;
  showCharacterCount?: boolean;
  showAIAssist?: boolean;
}

export function TipTapEditor({
  content = '',
  onChange,
  onSelectionChange,
  placeholder = '开始创作你的内容...',
  maxLength = 10000,
  className,
  editable = true,
  showToolbar = true,
  showCharacterCount = true,
  showAIAssist = true,
}: TipTapEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        codeBlock: false,
      }),
      Image.configure({
        inline: true,
        allowBase64: true,
      }),
      Placeholder.configure({
        placeholder,
      }),
      CharacterCount.configure({
        limit: maxLength,
      }),
      Link.configure({
        openOnClick: false,
        autolink: true,
      }),
      CodeBlockLowlight.configure({
        lowlight,
      }),
    ],
    content,
    editable,
    onUpdate: ({ editor }) => {
      onChange?.(editor.getHTML());
    },
    onSelectionUpdate: ({ editor }) => {
      const { from, to } = editor.state.selection;
      if (from !== to) {
        const text = editor.state.doc.textBetween(from, to, ' ');
        onSelectionChange?.(text);
      }
    },
  });

  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content);
    }
  }, [content, editor]);

  const handleImageUpload = useCallback(
    async (file: File) => {
      if (!editor) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        const base64 = e.target?.result as string;
        editor.chain().focus().setImage({ src: base64 }).run();
      };
      reader.readAsDataURL(file);
    },
    [editor]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const files = Array.from(e.dataTransfer.files);
      const imageFile = files.find((file) => file.type.startsWith('image/'));
      if (imageFile) {
        handleImageUpload(imageFile);
      }
    },
    [handleImageUpload]
  );

  const handlePaste = useCallback(
    (e: React.ClipboardEvent) => {
      const items = Array.from(e.clipboardData.items);
      const imageItem = items.find((item) => item.type.startsWith('image/'));
      if (imageItem) {
        e.preventDefault();
        const file = imageItem.getAsFile();
        if (file) {
          handleImageUpload(file);
        }
      }
    },
    [handleImageUpload]
  );

  if (!editor) {
    return null;
  }

  const characterCount = editor.storage.characterCount.characters();
  const wordCount = editor.storage.characterCount.words();

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {showToolbar && <EditorToolbar editor={editor} />}

      {showAIAssist && (
        <BubbleMenu
          editor={editor}
          shouldShow={({ editor, state }) => {
            const { from, to } = state.selection;
            return from !== to && !editor.isActive('image');
          }}
        >
          <AIAssistMenu editor={editor} />
        </BubbleMenu>
      )}

      <div
        className="flex-1 overflow-auto"
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onPaste={handlePaste}
      >
        <EditorContent
          editor={editor}
          className="prose prose-sm sm:prose lg:prose-lg max-w-none p-4 min-h-[300px] focus:outline-none"
        />
      </div>

      {showCharacterCount && (
        <div className="flex items-center justify-between px-4 py-2 text-xs text-muted-foreground border-t">
          <span>
            {characterCount} / {maxLength} 字符
          </span>
          <span>{wordCount} 词</span>
        </div>
      )}
    </div>
  );
}

export default TipTapEditor;
