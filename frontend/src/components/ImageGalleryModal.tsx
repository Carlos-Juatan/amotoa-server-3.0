import React, { useEffect, useCallback, useState } from 'react';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';

interface ImageGalleryModalProps {
  images: string[];
  initialIndex?: number;
  isOpen: boolean;
  onClose: () => void;
}

export const ImageGalleryModal: React.FC<ImageGalleryModalProps> = ({
  images,
  initialIndex = 0,
  isOpen,
  onClose,
}) => {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);

  useEffect(() => {
    if (isOpen) setCurrentIndex(initialIndex);
  }, [isOpen, initialIndex]);

  const goToPrev = useCallback(() => {
    setCurrentIndex((i) => (i > 0 ? i - 1 : images.length - 1));
  }, [images.length]);

  const goToNext = useCallback(() => {
    setCurrentIndex((i) => (i < images.length - 1 ? i + 1 : 0));
  }, [images.length]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') goToPrev();
      else if (e.key === 'ArrowRight') goToNext();
      else if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen, goToPrev, goToNext, onClose]);

  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  if (!isOpen || images.length === 0) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label="Image gallery"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/90 backdrop-blur-md" onClick={onClose} />

      {/* Modal container */}
      <div className="relative z-10 flex flex-col items-center w-full max-w-5xl px-4 max-h-screen py-12 gap-4">

        {/* Header */}
        <div className="w-full flex items-center justify-between px-2">
          <span className="text-slate-400 text-sm font-mono">
            {currentIndex + 1} / {images.length}
          </span>
          <button
            onClick={onClose}
            className="p-2 rounded-full glass-panel text-slate-300 hover:text-white hover:bg-white/10 transition-all duration-200"
            aria-label="Fechar galeria"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Main image */}
        <div className="relative flex items-center justify-center w-full flex-1 min-h-0">
          {images.length > 1 && (
            <button
              onClick={goToPrev}
              disabled={currentIndex === 0}
              className="absolute left-0 z-20 p-2 rounded-full glass-panel text-slate-300 hover:text-white hover:bg-white/10 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="Imagem anterior"
            >
              <ChevronLeft className="w-7 h-7" />
            </button>
          )}

          <div className="flex items-center justify-center w-full max-h-[65vh]">
            <img
              key={currentIndex}
              src={images[currentIndex]}
              alt={`Gallery image ${currentIndex + 1}`}
              className="max-h-[65vh] max-w-full object-contain rounded-lg shadow-2xl shadow-black/60"
              style={{ animation: 'fadeIn 0.25s ease' }}
            />
          </div>

          {images.length > 1 && (
            <button
              onClick={goToNext}
              disabled={currentIndex === images.length - 1}
              className="absolute right-0 z-20 p-2 rounded-full glass-panel text-slate-300 hover:text-white hover:bg-white/10 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="Próxima imagem"
            >
              <ChevronRight className="w-7 h-7" />
            </button>
          )}
        </div>

        {/* Thumbnail strip */}
        {images.length > 1 && (
          <div className="flex gap-2 overflow-x-auto max-w-full px-2 pb-1" style={{ scrollbarWidth: 'thin' }}>
            {images.map((src, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentIndex(idx)}
                className={`flex-none w-14 h-14 rounded overflow-hidden border-2 transition-all duration-200 ${
                  idx === currentIndex
                    ? 'border-blue-400 scale-110 shadow-md shadow-blue-400/40'
                    : 'border-slate-700 hover:border-slate-500 opacity-60 hover:opacity-100'
                }`}
                aria-label={`Ver imagem ${idx + 1}`}
              >
                <img src={src} alt={`Thumbnail ${idx + 1}`} className="w-full h-full object-cover" loading="lazy" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
