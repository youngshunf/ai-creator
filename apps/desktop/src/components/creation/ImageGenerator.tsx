/**
 * 配图生成组件
 * @author Ysf
 */
import { useState } from 'react';
import { Image, Loader2, RefreshCw, Download } from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';

interface ImageGeneratorProps {
  content: string;
  onImagesGenerated?: (images: string[]) => void;
}

export function ImageGenerator({ content, onImagesGenerated }: ImageGeneratorProps) {
  const [images, setImages] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [style, setStyle] = useState('modern');

  const handleGenerate = async () => {
    if (!content.trim()) return;
    setLoading(true);

    try {
      const result = await invoke<{ success: boolean; outputs: { images: string[] }; error?: string }>('execute_graph', {
        graphName: 'image-generation',
        inputs: { content: content.trim(), count: 3, style },
      });

      if (result.success && result.outputs?.images) {
        setImages(result.outputs.images);
        onImagesGenerated?.(result.outputs.images);
      }
    } catch (e) {
      console.error('生成配图失败:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <select
          value={style}
          onChange={(e) => setStyle(e.target.value)}
          className="px-3 py-2 text-sm border border-slate-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800"
        >
          <option value="modern">现代简约</option>
          <option value="illustration">插画风格</option>
          <option value="photo">摄影风格</option>
          <option value="flat">扁平设计</option>
        </select>
        <button
          onClick={handleGenerate}
          disabled={loading || !content.trim()}
          className="px-4 py-2 bg-primary-600 hover:bg-primary-500 disabled:bg-slate-300 text-white rounded-lg text-sm font-medium flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Image className="w-4 h-4" />}
          生成配图
        </button>
      </div>

      {images.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          {images.map((url, i) => (
            <div key={i} className="relative group aspect-square rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700">
              <img src={url} alt={`配图${i + 1}`} className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <button className="p-2 bg-white rounded-full">
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
